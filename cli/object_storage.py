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
        region_name='auto',
        config=Config(signature_version='s3v4'),
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


def delete_objects(keys: list[str]) -> None:
    """Delete specific objects.

    Never delete by prefix: the convention prefix is per convention-day and shared
    by every cosplayer, so a prefix delete would wipe a whole day's variants for
    everyone. Pass only the keys the server reported as orphaned.
    """
    if not keys:
        return
    config = get_config()
    client = _get_storage_client()
    bucket = config["object_storage_bucket_name"]
    for key in keys:
        client.delete_object(Bucket=bucket, Key=key)


def build_r2_keys(prefix: str, file: Path) -> tuple[str, str]:
    """Build R2 keys for thumbnail and preview variants only."""
    root_key = f"{prefix}/{file.stem}"
    return f"{root_key}/thumbnail.webp", f"{root_key}/preview.webp"
