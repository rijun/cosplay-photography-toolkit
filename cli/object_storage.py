import io
from pathlib import Path

import boto3
from botocore.config import Config

from cli.config import get_config


def _get_storage_client():
    config = get_config()
    return boto3.client(
        "s3",
        endpoint_url=config["object_storage_endpoint_url"],
        aws_access_key_id=config["object_storage_access_key_id"],
        aws_secret_access_key=config["object_storage_secret_access_key"],
        config=Config(signature_version="s3v4"),
    )


def upload_photo(photo_path: Path, object_key: str) -> None:
    config = get_config()
    client = _get_storage_client()
    content_type = "image/jpeg"
    if photo_path.suffix.lower() == ".png":
        content_type = "image/png"

    client.upload_file(
        str(photo_path),
        config["object_storage_bucket_name"],
        object_key,
        ExtraArgs={"ContentType": content_type},
    )


def upload_file_buffer(buffer: io.BytesIO, object_key: str) -> None:
    config = get_config()
    client = _get_storage_client()
    client.upload_fileobj(
      buffer,
      config["object_storage_bucket_name"],
      object_key,
      ExtraArgs={"ContentType": "image/webp"}
    )


def delete_gallery(prefix: str) -> None:
    config = get_config()
    client = _get_storage_client()
    objects = client.list_objects_v2(Bucket=config["object_storage_bucket_name"], Prefix=prefix)
    if 'Contents' not in objects:
        return
    for obj in objects['Contents']:
        client.delete_object(Bucket=config["object_storage_bucket_name"], Key=obj['Key'])


def build_keys(gallery_slug: str, file: Path) -> tuple[str, str, str]:
    root_key = f"{gallery_slug}/{file.stem}"
    return f"{root_key}/{file.name}", f"{root_key}/thumbnail.webp", f"{root_key}/preview.webp"
