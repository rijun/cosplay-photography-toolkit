import pathlib
from pathlib import Path
from urllib.parse import quote

import httpx

from cli.config import get_config


def _get_auth() -> tuple[str, str]:
    config = get_config()
    return config["nextcloud_username"], config["nextcloud_app_password"]


def _webdav_url() -> str:
    return get_config()["nextcloud_webdav_url"].rstrip("/")


def _encode_path(path: str) -> str:
    return "/".join(quote(segment, safe="") for segment in path.split("/"))


def ensure_directories(nextcloud_path: str) -> None:
    """Create all directories in the Nextcloud path via MKCOL."""
    auth = _get_auth()
    base = _webdav_url()
    parts = nextcloud_path.split("/")

    for i in range(1, len(parts) + 1):
        partial = "/".join(parts[:i])
        url = f"{base}/{_encode_path(partial)}"
        resp = httpx.request("MKCOL", url, auth=auth, timeout=30)
        # 405 = already exists, that's fine
        if resp.status_code not in (201, 405):
            resp.raise_for_status()


def upload_file(file_path: Path, nextcloud_path: str) -> None:
    """Upload a file to Nextcloud via WebDAV PUT."""
    auth = _get_auth()
    url = f"{_webdav_url()}/{_encode_path(nextcloud_path)}/{quote(file_path.name, safe='')}"

    with open(file_path, "rb") as f:
        resp = httpx.put(url, content=f, auth=auth, timeout=120)
    resp.raise_for_status()


def build_convention_path(convention_name: str, year: int, day: str, cosplayers: list[str]) -> str:
    """Build Nextcloud path for a convention photo.

    Returns e.g. "Conventions/2026/AnimeCon/Saturday/cosplayer_1 & cosplayer_2"
    """
    config = get_config()
    base_path = pathlib.Path(config["nextcloud_base_path"])
    cosplayer_str = " & ".join(sorted(c.lstrip("@") for c in cosplayers))
    return str(base_path / f"Conventions/{year}/{convention_name}/{day}/{cosplayer_str}")


def build_shooting_path(date_str: str, character: str) -> str:
    """Build Nextcloud path for a planned shooting.

    Returns e.g. "Shootings/2026-03-15 Rose Quartz"
    """
    config = get_config()
    base_path = pathlib.Path(config["nextcloud_base_path"])
    return str(base_path / f"Shootings/{date_str} {character}")
