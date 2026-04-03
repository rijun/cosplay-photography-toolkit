import os
import zipfile
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from gallery import nextcloud, object_storage
from gallery.models import Photo, ZipDownload


def _cleanup_expired_zips():
    """Delete DB records older than ZIP_DOWNLOAD_MAX_AGE_SECONDS and their R2 objects."""
    cutoff = timezone.now() - timedelta(seconds=settings.ZIP_DOWNLOAD_MAX_AGE_SECONDS)
    old_downloads = ZipDownload.objects.filter(created_at__lt=cutoff)
    client = object_storage.get_storage_client()
    bucket = settings.OBJECT_STORAGE_BUCKET_NAME
    for dl in old_downloads:
        if dl.r2_key:
            try:
                client.delete_object(Bucket=bucket, Key=dl.r2_key)
            except Exception:
                pass
    old_downloads.delete()

    # Also mark stale "processing" records as failed (worker likely died)
    stale_cutoff = timezone.now() - timedelta(hours=1)
    ZipDownload.objects.filter(
        status='processing', created_at__lt=stale_cutoff
    ).update(status='failed', error_message='Task timed out')


@shared_task(bind=True, max_retries=0, time_limit=3600, soft_time_limit=3300)
def build_zip(self, zip_download_id, photo_ids):
    """Fetch photos from Nextcloud, build a zip, upload to R2."""
    _cleanup_expired_zips()

    dl = ZipDownload.objects.get(id=zip_download_id)
    dl.status = 'processing'
    dl.celery_task_id = self.request.id
    dl.save(update_fields=['status', 'celery_task_id'])

    photos = list(Photo.objects.filter(id__in=photo_ids, gallery=dl.gallery))
    dl.progress_total = len(photos)
    dl.save(update_fields=['progress_total'])

    zip_dir = settings.ZIP_DOWNLOAD_DIR
    os.makedirs(zip_dir, exist_ok=True)
    zip_path = os.path.join(zip_dir, f"{zip_download_id}.zip")

    # Determine if we need an edited/ subfolder: only when the selection
    # contains a mix of originals and edited photos.
    has_originals = any(not p.is_edited for p in photos)
    has_edited = any(p.is_edited for p in photos)
    use_edited_subfolder = has_originals and has_edited

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
            for i, photo in enumerate(photos):
                data = nextcloud.download_file(photo.nextcloud_path, photo.filename)
                arcname = photo.filename
                if use_edited_subfolder and photo.is_edited:
                    arcname = f"edited/{photo.filename}"
                zf.writestr(arcname, data)
                dl.progress_current = i + 1
                dl.save(update_fields=['progress_current'])

        # Upload to R2
        r2_key = f"zip_downloads/{zip_download_id}.zip"
        client = object_storage.get_storage_client()
        client.upload_file(
            zip_path,
            settings.OBJECT_STORAGE_BUCKET_NAME,
            r2_key,
            ExtraArgs={'ContentType': 'application/zip'},
        )

        dl.status = 'completed'
        dl.r2_key = r2_key
        dl.file_size = os.path.getsize(zip_path)
        dl.completed_at = timezone.now()
        dl.save(update_fields=['status', 'r2_key', 'file_size', 'completed_at'])
    except Exception as e:
        dl.status = 'failed'
        dl.error_message = str(e)[:500]
        dl.save(update_fields=['status', 'error_message'])
        raise
    finally:
        # Always clean up local file
        if os.path.exists(zip_path):
            os.remove(zip_path)