from typing import Generator
from urllib.parse import quote

import httpx
from django.conf import settings


def _build_url(nextcloud_path: str, filename: str) -> str:
    encoded_path = "/".join(quote(segment, safe="") for segment in nextcloud_path.split("/"))
    encoded_filename = quote(filename, safe="")
    return f"{settings.NEXTCLOUD_WEBDAV_URL}/{encoded_path}/{encoded_filename}"


def download_file(nextcloud_path: str, filename: str) -> bytes:
    """Download a file from Nextcloud via WebDAV GET."""
    resp = httpx.get(
        _build_url(nextcloud_path, filename),
        auth=(settings.NEXTCLOUD_USERNAME, settings.NEXTCLOUD_APP_PASSWORD),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def download_file_stream(nextcloud_path: str, filename: str) -> Generator[bytes, None, None]:
    """Stream a file from Nextcloud via WebDAV GET in chunks."""
    with httpx.stream(
        'GET',
        _build_url(nextcloud_path, filename),
        auth=(settings.NEXTCLOUD_USERNAME, settings.NEXTCLOUD_APP_PASSWORD),
        timeout=120,
    ) as resp:
        resp.raise_for_status()
        yield from resp.iter_bytes(chunk_size=64 * 1024)
