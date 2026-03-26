from urllib.parse import quote

import httpx
from django.conf import settings


def download_file(nextcloud_path: str, filename: str) -> bytes:
    """Download a file from Nextcloud via WebDAV GET."""
    encoded_path = "/".join(quote(segment, safe="") for segment in nextcloud_path.split("/"))
    encoded_filename = quote(filename, safe="")
    url = f"{settings.NEXTCLOUD_WEBDAV_URL}/{encoded_path}/{encoded_filename}"

    resp = httpx.get(
        url,
        auth=(settings.NEXTCLOUD_USERNAME, settings.NEXTCLOUD_APP_PASSWORD),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def download_folder_zip(nextcloud_path: str):
    """Stream a Nextcloud folder as a ZIP file.

    Uses Nextcloud's built-in ZIP download endpoint.
    Returns an iterator of bytes chunks.
    """
    # Nextcloud's download endpoint serves folders as ZIPs
    base_url = settings.NEXTCLOUD_WEBDAV_URL.split("/remote.php/")[0]
    encoded_path = "/".join(quote(segment, safe="") for segment in nextcloud_path.split("/"))
    url = f"{base_url}/index.php/apps/files/ajax/download.php?dir=/{encoded_path}"

    with httpx.stream(
        "GET",
        url,
        auth=(settings.NEXTCLOUD_USERNAME, settings.NEXTCLOUD_APP_PASSWORD),
        timeout=300,
        follow_redirects=True,
    ) as resp:
        resp.raise_for_status()
        yield from resp.iter_bytes(chunk_size=65536)
