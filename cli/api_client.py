import httpx

from cli.config import get_config


class ApiClient:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=120,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def create_gallery(self, name: str, slug: str) -> dict:
        resp = self._client.post("/api/galleries", json={"name": name, "slug": slug})
        if resp.status_code == 409:
            # Gallery already exists, that's fine
            return {"name": name, "slug": slug, "existed": True}
        resp.raise_for_status()
        result = resp.json()
        result["existed"] = False
        return result

    def list_galleries(self) -> list[dict]:
        resp = self._client.get("/api/galleries")
        resp.raise_for_status()
        return resp.json()

    def delete_gallery(self, slug: str) -> dict:
        resp = self._client.delete("/api/galleries", params={"slug": slug})
        resp.raise_for_status()
        return resp.json()

    def register_photo(self, slug: str, filename: str, nextcloud_path: str, thumbnail_key: str, preview_key: str, display_order: int, is_edited: bool = False) -> dict:
        resp = self._client.post(
            f"/api/galleries/{slug}/photos",
            json={
                "filename": filename,
                "nextcloud_path": nextcloud_path,
                "thumbnail_key": thumbnail_key,
                "preview_key": preview_key,
                "display_order": display_order,
                "is_edited": is_edited,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def delete_photos(self, slug: str) -> dict:
        resp = self._client.delete(f"/api/galleries/{slug}/photos")
        resp.raise_for_status()
        return resp.json()

    def get_selections(self, slug: str, flag: int = 0) -> list[str]:
        resp = self._client.get(f"/api/galleries/{slug}/selections", params={"flag": flag})
        resp.raise_for_status()
        return resp.json()

    def archive_gallery(self, slug: str) -> dict:
        resp = self._client.patch(f"/api/galleries/{slug}/archive")
        resp.raise_for_status()
        return resp.json()


def get_client() -> ApiClient:
    config = get_config()
    return ApiClient(config["api_url"], config["api_key"])
