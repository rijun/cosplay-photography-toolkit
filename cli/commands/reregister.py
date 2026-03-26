import re
from collections import defaultdict

import click

from cli.api_client import get_client
from cli.nextcloud import list_directory, build_convention_path
from cli.object_storage import build_r2_keys
from cli.config import get_config


PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

GERMAN_TO_ENGLISH_DAYS = {
    "Montag": "Monday",
    "Dienstag": "Tuesday",
    "Mittwoch": "Wednesday",
    "Donnerstag": "Thursday",
    "Freitag": "Friday",
    "Samstag": "Saturday",
    "Sonntag": "Sunday",
}

GERMAN_DAYS_ABBREV = {
    "Montag": "Mo",
    "Dienstag": "Di",
    "Mittwoch": "Mi",
    "Donnerstag": "Do",
    "Freitag": "Fr",
    "Samstag": "Sa",
    "Sonntag": "So",
}


def _slugify_convention(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def _slugify_cosplayer(handle: str) -> str:
    handle = handle.lstrip("@").lower().strip()
    handle = re.sub(r"[^\w.\-]", "-", handle)
    handle = re.sub(r"-+", "-", handle)
    return handle.strip("-")


@click.command()
@click.argument("convention")
@click.argument("year", type=int)
@click.option("--edited", is_flag=True, default=False, help="Register as edited versions")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be registered without doing it")
def reregister(convention: str, year: int, edited: bool, dry_run: bool):
    """Re-register photos by scanning Nextcloud directories.

    Reads the folder structure under Conventions/{YEAR}/{CONVENTION}/ to rebuild
    gallery-to-photo mappings, then deletes existing photo records and re-registers.
    """
    config = get_config()
    base_path = config["nextcloud_base_path"]
    conv_path = f"{base_path}/Conventions/{year}/{convention}"
    conv_slug = _slugify_convention(convention)

    # List days
    click.echo(f"Scanning {conv_path}/...")
    try:
        days = list_directory(conv_path)
    except Exception as e:
        raise click.ClickException(f"Could not list {conv_path}: {e}")

    # For each day, list cosplayer folders, then list files in each
    # gallery_key → {slug, name, files: [(filename, nextcloud_path, thumb_key, preview_key)]}
    galleries: dict[str, dict] = {}
    # Track files per cosplayer folder to handle group photos
    # nextcloud_folder → list of filenames
    folder_files: dict[str, list[str]] = {}

    for day in days:
        day_abbrev = GERMAN_DAYS_ABBREV.get(day)
        if not day_abbrev:
            click.echo(f"  Skipping unknown day folder: {day}")
            continue

        day_path = f"{conv_path}/{day}"
        try:
            cosplayer_folders = list_directory(day_path)
        except Exception as e:
            click.echo(f"  Could not list {day_path}: {e}")
            continue

        for folder_name in cosplayer_folders:
            # Folder might be "cosplayer_1 & cosplayer_2" for group photos
            cosplayers = [c.strip() for c in folder_name.split(" & ")]
            folder_path = f"{day_path}/{folder_name}"

            try:
                files = list_directory(folder_path)
            except Exception as e:
                click.echo(f"  Could not list {folder_path}: {e}")
                continue

            photo_files = [f for f in files if any(f.lower().endswith(ext) for ext in PHOTO_EXTENSIONS)]
            if not photo_files:
                continue

            folder_files[folder_path] = photo_files
            nc_path = build_convention_path(convention, year, day, cosplayers)

            for cosplayer in cosplayers:
                cos_slug = _slugify_cosplayer(cosplayer)
                slug = f"{conv_slug}-{day_abbrev.lower()}-{cos_slug}"
                if len(slug) > 80:
                    slug = slug[:80].rstrip("-")
                name = f"{convention} \u2013 {day} \u2013 {cosplayer}"

                if slug not in galleries:
                    galleries[slug] = {"slug": slug, "name": name, "photos": []}

                r2_prefix = f"{conv_slug}-{day_abbrev.lower()}"
                for filename in photo_files:
                    stem = filename.rsplit(".", 1)[0]
                    thumb_key = f"{r2_prefix}/{stem}/thumbnail.webp"
                    preview_key = f"{r2_prefix}/{stem}/preview.webp"
                    galleries[slug]["photos"].append({
                        "filename": filename,
                        "nextcloud_path": nc_path,
                        "thumbnail_key": thumb_key,
                        "preview_key": preview_key,
                    })

    if not galleries:
        click.echo("No photos found.")
        return

    # Show summary
    total_registrations = sum(len(g["photos"]) for g in galleries.values())
    unique_files = {p["filename"] for g in galleries.values() for p in g["photos"]}
    click.echo(f"\nFound {len(galleries)} galleries, {len(unique_files)} unique photos, {total_registrations} registrations:")
    for slug in sorted(galleries):
        g = galleries[slug]
        click.echo(f"  {g['name']:50s} \u2014 {len(g['photos'])} photos")
    if edited:
        click.echo("  Registering as EDITED versions.")

    if dry_run:
        click.echo("\nDry run \u2014 no changes made.")
        return

    click.confirm("\nReady to delete existing photos and re-register?", abort=True)

    with get_client() as client:
        for slug in sorted(galleries):
            g = galleries[slug]
            # Ensure gallery exists
            try:
                client.create_gallery(g["name"], g["slug"])
            except Exception as e:
                click.echo(f"  Warning: could not create '{g['slug']}': {e}")
            # Delete existing photos
            try:
                result = client.delete_photos(g["slug"])
                deleted = result.get("deleted", 0)
                if deleted:
                    click.echo(f"  Deleted {deleted} existing photo(s) from '{g['slug']}'")
            except Exception as e:
                click.echo(f"  Warning: could not delete photos from '{g['slug']}': {e}")
            # Re-register (update_or_create handles duplicates gracefully)
            for i, photo in enumerate(sorted(g["photos"], key=lambda p: p["filename"]), 1):
                client.register_photo(
                    g["slug"], photo["filename"],
                    photo["nextcloud_path"],
                    photo["thumbnail_key"], photo["preview_key"],
                    display_order=i, is_edited=edited,
                )
            click.echo(f"  Registered {len(g['photos'])} photo(s) in '{g['slug']}'")

    click.echo("Done.")
