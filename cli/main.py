import re
from pathlib import Path
from urllib.parse import urlparse

import click

from cli import api_client
from cli.config import get_config, load_config, save_config
from cli.exporter import export_selections
from cli.metadata import strip_metadata
from cli.object_storage import upload_photo, delete_gallery

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


@click.group()
def cli():
    """Photo gallery CLI for managing galleries and uploading photos."""
    pass


@cli.command()
def configure():
    """Set up CLI configuration."""
    config = load_config()
    config["api_url"] = click.prompt("App API URL", default=config.get("api_url", ""))
    config["api_key"] = click.prompt("API key", default=config.get("api_key", ""))
    config["object_storage_endpoint_url"] = click.prompt("Object storage endpoint URL", default=config.get("object_storage_endpoint_url", ""))
    config["object_storage_access_key_id"] = click.prompt("Object storage access key ID", default=config.get("object_storage_access_key_id", ""))
    config["object_storage_secret_access_key"] = click.prompt("Object storage secret access key",
                                                  default=config.get("object_storage_secret_access_key", ""))
    config["object_storage_bucket_name"] = click.prompt("Object storage bucket name", default=config.get("object_storage_bucket_name", ""))
    save_config(config)
    click.echo("Configuration saved.")


@cli.group()
def gallery():
    """Manage galleries."""
    pass


@gallery.command("create")
@click.argument("name")
def gallery_create(name: str):
    """Create a new gallery."""
    slug = _slugify(name)
    result = api_client.create_gallery(name, slug)
    click.echo(f"Gallery created: {result['name']}")
    click.echo(f"Slug: {result['slug']}")
    click.echo(f"URL: {_base_url()}/g/{result['token']}")


@gallery.command("list")
def gallery_list():
    """List all galleries."""
    galleries = api_client.list_galleries()
    if not galleries:
        click.echo("No galleries found.")
        return
    base = _base_url()
    for g in galleries:
        click.echo(f"  {g['slug']:30s}  {base}/g/{g['token']}")


@gallery.command("delete")
@click.argument("gallery_slug")
def gallery_delete(gallery_slug: str):
    """Delete a gallery."""
    galleries = api_client.list_galleries()
    if gallery_slug not in [g['slug'] for g in galleries]:
        click.echo(f"Gallery with slug '{gallery_slug}' does not exist.",)
        return
    result = api_client.delete_gallery(gallery_slug)
    delete_gallery(gallery_slug)
    click.echo(f"Gallery {result['slug']} deleted.")


@gallery.command("archive")
@click.argument("gallery_slug")
def gallery_archive(gallery_slug: str):
    """Archive a gallery (set is_active=False)."""
    result = api_client.archive_gallery(gallery_slug)
    click.echo(f"Gallery '{result['name']}' archived.")


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--gallery", "-g", "gallery_slug", required=True, help="Gallery slug")
def upload(path: Path, gallery_slug: str):
    """Upload photos to a gallery."""
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

    click.echo(f"Uploading {len(files)} photo(s) to '{gallery_slug}'...")

    for i, photo_path in enumerate(files, 1):
        click.echo(f"  [{i}/{len(files)}] {photo_path.name}")

        # Strip metadata
        # strip_metadata(photo_path)

        # Upload to object storage
        object_key = f"{gallery_slug}/{photo_path.name}"
        upload_photo(photo_path, object_key)

        # Register with app
        api_client.register_photo(gallery_slug, photo_path.name, object_key, display_order=i)

    click.echo("Done.")


@cli.group()
def export():
    """Export data from galleries."""
    pass


@export.command("selections")
@click.argument("slug")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=".", help="Output directory")
def export_selections_cmd(slug: str, output: Path):
    """Export selected photo filenames to a text file."""
    output_path = export_selections(slug, output)
    click.echo(f"Selections exported to {output_path}")


def _base_url() -> str:
    parsed = urlparse(get_config()["api_url"])
    return f"{parsed.scheme}://{parsed.netloc}"


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")
