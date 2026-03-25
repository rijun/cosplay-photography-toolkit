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
