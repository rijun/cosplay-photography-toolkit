import httpx

from cli.config import get_config


class ApiClient:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-Api-Key": api_key},
            timeout=30,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def create_gallery(self, name: str, slug: str) -> dict:
        resp = self._client.post("/api/galleries", json={"name": name, "slug": slug})
        resp.raise_for_status()
        return resp.json()

    def list_galleries(self) -> list[dict]:
        resp = self._client.get("/api/galleries")
        resp.raise_for_status()
        return resp.json()

    def delete_gallery(self, slug: str) -> dict:
        resp = self._client.delete("/api/galleries", params={"slug": slug})
        resp.raise_for_status()
        return resp.json()

    def register_photo(self, slug: str, filename: str, object_key: str, thumbnail_key: str, preview_key: str, display_order: int) -> dict:
        resp = self._client.post(
            f"/api/galleries/{slug}/photos",
            json={
                "filename": filename,
                "object_key": object_key,
                "thumbnail_key": thumbnail_key,
                "preview_key": preview_key,
                "display_order": display_order,
            },
        )
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
