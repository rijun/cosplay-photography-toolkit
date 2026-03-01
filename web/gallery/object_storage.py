import boto3
from botocore.config import Config
from django.conf import settings

_storage_client = None


def get_storage_client():
    """Get or create a cached S3-compatible storage client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = boto3.client(
            's3',
            endpoint_url=settings.OBJECT_STORAGE_ENDPOINT_URL,
            aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
        )
    return _storage_client


def photo_url(object_key: str) -> str:
    """Generate a URL for a photo stored in object storage.

    Uses public URL if configured, otherwise generates a signed URL.
    """
    if settings.OBJECT_STORAGE_PUBLIC_URL:
        return f"{settings.OBJECT_STORAGE_PUBLIC_URL}/{object_key}"

    return get_storage_client().generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.OBJECT_STORAGE_BUCKET_NAME, 'Key': object_key},
        ExpiresIn=3600,
    )
