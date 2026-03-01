import httpx

from cli.config import get_config


def _client() -> httpx.Client:
    config = get_config()
    return httpx.Client(
        base_url=config["api_url"],
        headers={"X-Api-Key": config["api_key"]},
        timeout=30,
    )


def create_gallery(name: str, slug: str) -> dict:
    with _client() as client:
        resp = client.post("/api/galleries", json={"name": name, "slug": slug})
        resp.raise_for_status()
        return resp.json()


def list_galleries() -> list[dict]:
    with _client() as client:
        resp = client.get("/api/galleries")
        resp.raise_for_status()
        return resp.json()


def delete_gallery(slug: str):
    with _client() as client:
        resp = client.delete("/api/galleries", params={"slug": slug})
        resp.raise_for_status()
        return resp.json()


def register_photo(slug: str, filename: str, object_key: str, display_order: int) -> dict:
    with _client() as client:
        resp = client.post(
            f"/api/galleries/{slug}/photos",
            json={"filename": filename, "object_key": object_key, "display_order": display_order},
        )
        resp.raise_for_status()
        return resp.json()


def get_selections(slug: str) -> list[str]:
    with _client() as client:
        resp = client.get(f"/api/galleries/{slug}/selections")
        resp.raise_for_status()
        return resp.json()


def archive_gallery(slug: str) -> dict:
    with _client() as client:
        resp = client.patch(f"/api/galleries/{slug}/archive")
        resp.raise_for_status()
        return resp.json()
