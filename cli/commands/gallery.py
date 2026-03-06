import re
from urllib.parse import urlparse

import click

from cli.api_client import get_client
from cli.config import get_config
from cli.object_storage import delete_gallery as delete_gallery_objects


@click.group()
def gallery():
    """Manage galleries."""
    pass


@gallery.command("create")
@click.argument("name")
def gallery_create(name: str):
    """Create a new gallery."""
    slug = _slugify(name)
    with get_client() as client:
        result = client.create_gallery(name, slug)
    click.echo(f"Gallery created: {result['name']}")
    click.echo(f"Slug: {result['slug']}")
    click.echo(f"URL: {_base_url()}/g/{result['token']}")


@gallery.command("list")
def gallery_list():
    """List all galleries."""
    with get_client() as client:
        galleries = client.list_galleries()
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
    with get_client() as client:
        galleries = client.list_galleries()
        if gallery_slug not in [g["slug"] for g in galleries]:
            click.echo(f"Gallery with slug '{gallery_slug}' does not exist.")
            return
        result = client.delete_gallery(gallery_slug)
    delete_gallery_objects(gallery_slug)
    click.echo(f"Gallery {result['slug']} deleted.")


@gallery.command("archive")
@click.argument("gallery_slug")
def gallery_archive(gallery_slug: str):
    """Archive a gallery (set is_active=False)."""
    with get_client() as client:
        result = client.archive_gallery(gallery_slug)
    click.echo(f"Gallery '{result['name']}' archived.")


def _base_url() -> str:
    parsed = urlparse(get_config()["api_url"])
    return f"{parsed.scheme}://{parsed.netloc}"


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")
