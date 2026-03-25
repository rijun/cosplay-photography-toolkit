from pathlib import Path
import json

CONFIG_PATH = Path.home() / ".config" / "cosplay-photography-toolkit" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_config() -> dict:
    config = load_config()
    required = ["api_url", "api_key", "object_storage_endpoint_url", "object_storage_access_key_id",
                 "object_storage_secret_access_key", "object_storage_bucket_name",
                 "nextcloud_webdav_url", "nextcloud_username", "nextcloud_app_password", "nextcloud_base_path"]
    missing = [k for k in required if k not in config]
    if missing:
        raise SystemExit(
            f"Missing CLI config keys: {', '.join(missing)}\n"
            f"Run 'photo configure' to set up."
        )
    return config
