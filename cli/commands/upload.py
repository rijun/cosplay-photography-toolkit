import json
import re
import subprocess
import concurrent.futures
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click

from cli.api_client import get_client
from cli.image_processing import make_variant, THUMB_WIDTH, MEDIUM_WIDTH
from cli.nextcloud import upload_file, ensure_directories, build_convention_path, build_shooting_path
from cli.object_storage import upload_file_buffer, build_r2_keys

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

GERMAN_DAYS = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag",
}

GERMAN_DAYS_ABBREV = {
    "Monday": "Mo",
    "Tuesday": "Di",
    "Wednesday": "Mi",
    "Thursday": "Do",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "So",
}

def _slugify_convention(name: str) -> str:
    """Slugify convention name: lowercase, special chars to hyphens."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def _slugify_cosplayer(handle: str) -> str:
    """Slugify cosplayer handle: strip @, lowercase, keep dots/underscores."""
    handle = handle.lstrip("@").lower().strip()
    # Replace spaces and special chars (except dots, underscores, hyphens) with hyphens
    handle = re.sub(r"[^\w.\-]", "-", handle)
    handle = re.sub(r"-+", "-", handle)
    return handle.strip("-")


def _read_metadata(path: Path) -> list[dict]:
    """Run exiftool once to read IPTC:Keywords and DateTimeOriginal from all files."""
    result = subprocess.run(
        ["exiftool", "-IPTC:Keywords", "-DateTimeOriginal", "-json", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise click.ClickException(f"exiftool failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _parse_cosplayers(keywords) -> list[str]:
    """Extract cosplayer handles from IPTC Keywords field.

    Keywords can be a list or a comma-separated string.
    """
    if not keywords:
        return []
    if isinstance(keywords, list):
        return [k.strip() for k in keywords if k.strip()]
    # Single string, possibly comma-separated
    return [k.strip() for k in str(keywords).split(",") if k.strip()]


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse DateTimeOriginal string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _collect_files(path: Path) -> list[Path]:
    """Collect photo files from a path."""
    if path.is_file():
        return [path]
    files = sorted(
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in PHOTO_EXTENSIONS
    )
    return files


def _process_file(file: Path, nextcloud_path: str, thumbnail_key: str, preview_key: str) -> None:
    """Upload original to Nextcloud and variants to R2."""
    upload_file(file, nextcloud_path)
    upload_file_buffer(make_variant(file, THUMB_WIDTH), thumbnail_key)
    upload_file_buffer(make_variant(file, MEDIUM_WIDTH), preview_key)


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--convention", "-c", default=None, help="Convention name (convention mode)")
@click.option("--shooting", is_flag=True, default=False, help="Planned shooting mode")
@click.option("--edited", is_flag=True, default=False, help="Mark uploads as edited versions")
@click.option("--dry-run", is_flag=True, default=False, help="Show upload plan without uploading")
def upload(path: Path, convention: str | None, shooting: bool, edited: bool, dry_run: bool):
    """Upload photos with auto-grouping by cosplayer (convention) or as a single gallery (shooting)."""
    if not convention and not shooting:
        raise click.UsageError("Specify either --convention/-c or --shooting.")
    if convention and shooting:
        raise click.UsageError("Cannot use both --convention and --shooting.")

    files = _collect_files(path)
    if not files:
        click.echo("No photo files found.")
        return

    # Read metadata from all files at once
    click.echo("Reading metadata...")
    metadata = _read_metadata(path if path.is_dir() else path.parent)
    meta_by_file = {}
    for entry in metadata:
        source = Path(entry.get("SourceFile", ""))
        meta_by_file[source.name] = entry

    if shooting:
        _upload_shooting(path, files, meta_by_file, edited, dry_run)
    else:
        _upload_convention(path, files, meta_by_file, convention, edited, dry_run)


def _get_file_day(entry: dict) -> tuple[str, str, int]:
    """Get German day (full + abbrev) and year from a metadata entry.

    Returns (day_full, day_abbrev, year).
    """
    capture_date = _parse_date(entry.get("DateTimeOriginal"))
    if capture_date:
        day_en = capture_date.strftime('%A')
        return (
            GERMAN_DAYS.get(day_en, day_en),
            GERMAN_DAYS_ABBREV.get(day_en, capture_date.strftime('%a')),
            capture_date.year,
        )
    return ("Unbekannt", "unknown", datetime.now().year)


def _upload_convention(path: Path, files: list[Path], meta_by_file: dict,
                       convention: str, edited: bool, dry_run: bool):
    """Convention mode: auto-group by day + cosplayer, one gallery per combination."""
    # Group photos by (day, cosplayer) — each file gets its own day from EXIF
    # Key: (day_full, day_abbrev, cosplayer) → list of files
    gallery_photos: dict[tuple[str, str, str], list[Path]] = defaultdict(list)
    file_day: dict[Path, tuple[str, str, int]] = {}  # file → (day_full, day_abbrev, year)
    skipped = []
    year: int = datetime.now().year

    for file in files:
        entry = meta_by_file.get(file.name, {})

        day_full, day_abbrev, file_year = _get_file_day(entry)
        file_day[file] = (day_full, day_abbrev, file_year)
        year = file_year  # last seen year (they should all be the same convention year)

        keywords = entry.get("Keywords")
        cosplayers = _parse_cosplayers(keywords)

        if not cosplayers:
            skipped.append(file)
            continue

        for cosplayer in cosplayers:
            gallery_photos[(day_full, day_abbrev, cosplayer)].append(file)

    if not gallery_photos:
        click.echo("No photos with cosplayer keywords found.")
        if skipped:
            click.echo(f"  {len(skipped)} photo(s) had no keywords and were skipped.")
        return

    conv_slug = _slugify_convention(convention)

    # Build gallery info for each (day, cosplayer) combination
    galleries: dict[tuple[str, str, str], dict] = {}
    for (day_full, day_abbrev, cosplayer) in sorted(gallery_photos.keys()):
        cos_slug = _slugify_cosplayer(cosplayer)
        slug = f"{conv_slug}-{day_abbrev.lower()}-{cos_slug}"
        if len(slug) > 80:
            slug = slug[:80].rstrip("-")
        cos_display = cosplayer.lstrip("@")
        name = f"{convention} \u2013 {day_full} \u2013 {cos_display}"
        galleries[(day_full, day_abbrev, cosplayer)] = {"slug": slug, "name": name}

    # Build Nextcloud path per file (based on ALL cosplayers tagged on that file + its day)
    file_nextcloud_path: dict[Path, str] = {}
    for file in files:
        entry = meta_by_file.get(file.name, {})
        cosplayers = _parse_cosplayers(entry.get("Keywords"))
        if cosplayers:
            day_full, _, file_year = file_day[file]
            file_nextcloud_path[file] = build_convention_path(convention, file_year, day_full, cosplayers)

    # Count unique files
    all_unique_files = set()
    for photo_files in gallery_photos.values():
        all_unique_files.update(photo_files)

    group_photo_count = sum(1 for f in all_unique_files if sum(1 for photos in gallery_photos.values() if f in photos) > 1)

    # Collect days for summary
    days_seen = sorted({day_full for (day_full, _, _) in gallery_photos.keys()})

    # Show summary
    click.echo(f"\nFound {len(gallery_photos)} gallery/galleries across {len(all_unique_files)} photos ({', '.join(days_seen)}):")
    for (day_full, day_abbrev, cosplayer) in sorted(gallery_photos.keys()):
        cos_display = cosplayer.lstrip("@")
        count = len(gallery_photos[(day_full, day_abbrev, cosplayer)])
        click.echo(f"  {day_full:12s} {cos_display:30s} \u2014 {count} photos")
    if group_photo_count:
        click.echo(f"  ({group_photo_count} group photos will appear in multiple galleries)")
    if skipped:
        click.echo(f"  ({len(skipped)} photos without keywords will be skipped)")
    if edited:
        click.echo("  Uploading as EDITED versions.")

    # Show Nextcloud paths
    nc_paths = sorted(set(file_nextcloud_path.values()))
    click.echo(f"\nNextcloud upload paths:")
    for nc_path in nc_paths:
        count = sum(1 for p in file_nextcloud_path.values() if p == nc_path)
        click.echo(f"  {nc_path}/ ({count} files)")

    if dry_run:
        click.echo("\nDry run — no uploads performed.")
        return

    click.confirm("\nReady to process?", abort=True)

    # Strip Lightroom metadata (after reading keywords)
    click.echo("Stripping Lightroom metadata...")
    exiftool_res = subprocess.run(
        ["exiftool", "-IPTC:Keywords=", "-XMP:Subject=", "-XMP:WeightedFlatSubject=",
         "-rating=", "-label=", "-ext", "jpg", "-overwrite_original", "-P", str(path)]
    )
    if exiftool_res.returncode != 0:
        click.echo("Warning: exiftool strip failed, continuing anyway.")

    # Create galleries via API
    click.echo("Creating galleries...")
    with get_client() as client:
        for key, info in galleries.items():
            result = client.create_gallery(info["name"], info["slug"])
            if result.get("existed"):
                click.echo(f"  Gallery '{info['slug']}' already exists, will add photos to it.")
            else:
                click.echo(f"  Created gallery '{info['slug']}'")

    # Pre-create Nextcloud directories
    click.echo("Creating Nextcloud directories...")
    for nc_path in nc_paths:
        ensure_directories(nc_path)

    # Build R2 keys per file (thumbnail + preview only)
    # Use day-specific prefix so R2 keys don't collide across days
    file_r2_keys: dict[Path, tuple[str, str]] = {}
    for file in all_unique_files:
        _, day_abbrev, _ = file_day[file]
        r2_prefix = f"{conv_slug}-{day_abbrev.lower()}"
        file_r2_keys[file] = build_r2_keys(r2_prefix, file)

    # Upload files: originals to Nextcloud, variants to R2
    click.echo(f"\nUploading {len(all_unique_files)} unique photo(s)...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(
                _process_file, file,
                file_nextcloud_path[file],
                *file_r2_keys[file],
            ): file
            for file in all_unique_files
        }
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()
            except Exception as exc:
                click.echo(f"  ERROR {file.name}: {exc}")
            else:
                click.echo(f"  Done {file.name}")

    # Register photos in each gallery
    click.echo("Registering photos in galleries...")
    with get_client() as client:
        for key in sorted(gallery_photos.keys()):
            info = galleries[key]
            photos = gallery_photos[key]
            for i, file in enumerate(sorted(photos, key=lambda f: f.name), 1):
                thumbnail_key, preview_key = file_r2_keys[file]
                client.register_photo(
                    info["slug"], file.name,
                    file_nextcloud_path[file],
                    thumbnail_key, preview_key,
                    display_order=i, is_edited=edited,
                )
            click.echo(f"  Registered {len(photos)} photo(s) in '{info['slug']}'")

    click.echo("Done.")


def _upload_shooting(path: Path, files: list[Path], meta_by_file: dict,
                     edited: bool, dry_run: bool):
    """Shooting mode: one gallery for the entire shoot."""
    # Get capture date from first file
    capture_date: datetime | None = None
    for file in files:
        entry = meta_by_file.get(file.name, {})
        capture_date = _parse_date(entry.get("DateTimeOriginal"))
        if capture_date:
            break

    if capture_date:
        date_str = capture_date.strftime("%Y-%m-%d")
    else:
        click.echo("Warning: Could not determine capture date from EXIF.")
        date_str = click.prompt("Shooting date (YYYY-MM-DD)")

    character = click.prompt("Character name")

    nc_path = build_shooting_path(date_str, character)
    gallery_slug = _slugify_convention(f"{date_str}-{character}")
    if len(gallery_slug) > 80:
        gallery_slug = gallery_slug[:80].rstrip("-")
    gallery_name = f"{date_str} {character}"

    # Show summary
    click.echo(f"\nShooting: {gallery_name}")
    click.echo(f"  Gallery slug: {gallery_slug}")
    click.echo(f"  Nextcloud path: {nc_path}/")
    click.echo(f"  {len(files)} photo(s)")
    if edited:
        click.echo("  Uploading as EDITED versions.")

    if dry_run:
        click.echo("\nDry run — no uploads performed.")
        return

    click.confirm("\nReady to process?", abort=True)

    # Strip Lightroom metadata
    click.echo("Stripping Lightroom metadata...")
    exiftool_res = subprocess.run(
        ["exiftool", "-IPTC:Keywords=", "-XMP:Subject=", "-XMP:WeightedFlatSubject=",
         "-rating=", "-label=", "-ext", "jpg", "-overwrite_original", "-P", str(path)]
    )
    if exiftool_res.returncode != 0:
        click.echo("Warning: exiftool strip failed, continuing anyway.")

    # Create gallery
    click.echo("Creating gallery...")
    with get_client() as client:
        result = client.create_gallery(gallery_name, gallery_slug)
        if result.get("existed"):
            click.echo(f"  Gallery '{gallery_slug}' already exists, will add photos to it.")
        else:
            click.echo(f"  Created gallery '{gallery_slug}'")

    # Pre-create Nextcloud directory
    click.echo("Creating Nextcloud directory...")
    ensure_directories(nc_path)

    # Build R2 keys
    file_r2_keys = {file: build_r2_keys(gallery_slug, file) for file in files}

    # Upload files
    click.echo(f"\nUploading {len(files)} photo(s)...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(
                _process_file, file,
                nc_path,
                *file_r2_keys[file],
            ): file
            for file in files
        }
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()
            except Exception as exc:
                click.echo(f"  ERROR {file.name}: {exc}")
            else:
                click.echo(f"  Done {file.name}")

    # Register photos
    click.echo("Registering photos...")
    with get_client() as client:
        for i, file in enumerate(sorted(files, key=lambda f: f.name), 1):
            thumbnail_key, preview_key = file_r2_keys[file]
            client.register_photo(
                gallery_slug, file.name,
                nc_path, thumbnail_key, preview_key,
                display_order=i, is_edited=edited,
            )
        click.echo(f"  Registered {len(files)} photo(s) in '{gallery_slug}'")

    click.echo("Done.")
