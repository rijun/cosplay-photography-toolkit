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
from cli.object_storage import upload_photo, upload_file_buffer, build_keys

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

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


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--convention", "-c", required=True, help="Convention name")
@click.option("--edited", is_flag=True, default=False, help="Mark uploads as edited versions")
def upload(path: Path, convention: str, edited: bool):
    """Upload photos with auto-grouping by cosplayer."""
    # Collect photo files
    if path.is_file():
        files = [path]
    else:
        files = sorted(
            f for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in PHOTO_EXTENSIONS
        )
    if not files:
        click.echo("No photo files found.")
        return

    # Read metadata from all files at once
    click.echo("Reading metadata...")
    metadata = _read_metadata(path if path.is_dir() else path.parent)

    # Build lookup by filename
    meta_by_file = {}
    for entry in metadata:
        source = Path(entry.get("SourceFile", ""))
        meta_by_file[source.name] = entry

    # Group photos by cosplayer
    cosplayer_photos: dict[str, list[Path]] = defaultdict(list)
    skipped = []
    capture_date: datetime | None = None

    for file in files:
        entry = meta_by_file.get(file.name, {})

        # Get capture date from first file that has it
        if capture_date is None:
            capture_date = _parse_date(entry.get("DateTimeOriginal"))

        keywords = entry.get("Keywords")
        cosplayers = _parse_cosplayers(keywords)

        if not cosplayers:
            skipped.append(file)
            continue

        for cosplayer in cosplayers:
            cosplayer_photos[cosplayer].append(file)

    if not cosplayer_photos:
        click.echo("No photos with cosplayer keywords found.")
        if skipped:
            click.echo(f"  {len(skipped)} photo(s) had no keywords and were skipped.")
        return

    # Determine day of week
    if capture_date:
        day_abbrev = capture_date.strftime('%a')
        day_full = capture_date.strftime('%A')
    else:
        click.echo("Warning: Could not determine capture date, using 'unknown' for day.")
        day_abbrev = "unknown"
        day_full = "Unknown"

    conv_slug = _slugify_convention(convention)

    # Build gallery info for each cosplayer
    galleries: dict[str, dict] = {}
    for cosplayer in sorted(cosplayer_photos.keys()):
        cos_slug = _slugify_cosplayer(cosplayer)
        slug = f"{conv_slug}-{day_abbrev}-{cos_slug}"
        if len(slug) > 80:
            slug = slug[:80].rstrip("-")
        cos_display = cosplayer.lstrip("@")
        name = f"{convention} \u2013 {day_full} \u2013 {cos_display}"
        galleries[cosplayer] = {"slug": slug, "name": name}

    # Count unique files and group photos
    all_unique_files = set()
    for photo_files in cosplayer_photos.values():
        all_unique_files.update(photo_files)

    group_photo_count = sum(1 for f in all_unique_files if sum(1 for photos in cosplayer_photos.values() if f in photos) > 1)

    # Show summary
    click.echo(f"\nFound {len(cosplayer_photos)} cosplayer(s) across {len(all_unique_files)} photos ({day_full}):")
    for cosplayer in sorted(cosplayer_photos.keys()):
        cos_display = cosplayer.lstrip("@")
        count = len(cosplayer_photos[cosplayer])
        click.echo(f"  {cos_display:30s} \u2014 {count} photos")
    if group_photo_count:
        click.echo(f"  ({group_photo_count} group photos will appear in multiple galleries)")
    if skipped:
        click.echo(f"  ({len(skipped)} photos without keywords will be skipped)")
    if edited:
        click.echo("  Uploading as EDITED versions.")

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
        for cosplayer, info in galleries.items():
            result = client.create_gallery(info["name"], info["slug"])
            if result.get("existed"):
                click.echo(f"  Gallery '{info['slug']}' already exists, will add photos to it.")
            else:
                click.echo(f"  Created gallery '{info['slug']}'")

    # Upload unique files to R2 (once per file, using convention-based prefix)
    r2_prefix = f"{conv_slug}-{day_abbrev}"
    file_keys = {file: build_keys(r2_prefix, file) for file in all_unique_files}

    click.echo(f"\nUploading {len(all_unique_files)} unique photo(s) to storage...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(_process_file, file, *keys): file
            for file, keys in file_keys.items()
        }
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()
            except Exception as exc:
                click.echo(f"  ERROR {file.name}: {exc}")
            else:
                click.echo(f"  Done {file.name}")

    # Register photos in each cosplayer's gallery
    click.echo("Registering photos in galleries...")
    with get_client() as client:
        for cosplayer in sorted(cosplayer_photos.keys()):
            info = galleries[cosplayer]
            photos = cosplayer_photos[cosplayer]
            for i, file in enumerate(sorted(photos, key=lambda f: f.name), 1):
                object_key, thumbnail_key, preview_key = file_keys[file]
                client.register_photo(
                    info["slug"], file.name,
                    object_key, thumbnail_key, preview_key,
                    display_order=i, is_edited=edited,
                )
            click.echo(f"  Registered {len(photos)} photo(s) in '{info['slug']}'")

    click.echo("Done.")


def _process_file(file: Path, object_key: str, thumbnail_key: str, preview_key: str) -> None:
    upload_photo(file, object_key)
    upload_file_buffer(make_variant(file, THUMB_WIDTH), thumbnail_key)
    upload_file_buffer(make_variant(file, MEDIUM_WIDTH), preview_key)
