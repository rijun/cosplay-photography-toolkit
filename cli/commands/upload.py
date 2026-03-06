import subprocess
import concurrent.futures
from pathlib import Path

import click

from cli.api_client import get_client
from cli.image_processing import make_variant, THUMB_WIDTH, MEDIUM_WIDTH
from cli.object_storage import upload_photo, upload_file_buffer

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--gallery", "-g", "gallery_slug", required=True, help="Gallery slug")
def upload(path: Path, gallery_slug: str):
    """Upload photos to a gallery."""
    # Check if source folder and files exist
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
    click.confirm("Ready to process photos?", abort=True)

    # Remove unnecessary exif data (e.g. Lightroom ratings and tags)
    exiftool_res = subprocess.run(["exiftool", "-IPTC:Keywords=", "-XMP:Subject=", "-XMP:WeightedFlatSubject=", "-rating=", "-label=", "-ext", "pg", "-overwrite_original", "-P", path])
    if exiftool_res.returncode != 0:
        click.echo("Exiftool failed.")
        return

    # Upload files to the object storage
    click.echo(f"Uploading {len(files)} photo(s) to '{gallery_slug}'...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(_process_file, file, gallery_slug): file for file in files}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()
            except Exception as exc:
                click.echo(f"  ERROR {file.name}: {exc}")
            else:
                click.echo(f"  Done {file.name}")

    # Register files with gallery
    with get_client() as client:
        for i, file in enumerate(files, 1):
            # click.echo(f"  [{i}/{len(files)}] {file.name}")
            # upload_photo(file, object_key)
            client.register_photo(gallery_slug, file.name, display_order=i)

    click.echo("Done.")


def _process_file(file: Path, gallery_slug: str) -> None:
    upload_photo(file, f"{gallery_slug}/full-res/{file.name}")
    upload_file_buffer(make_variant(file, THUMB_WIDTH), f"{gallery_slug}/thumbnails/{file.stem}.webp")
    upload_file_buffer(make_variant(file, MEDIUM_WIDTH), f"{gallery_slug}/previews/{file.stem}.webp")