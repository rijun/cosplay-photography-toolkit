import json
from urllib.parse import quote

import nh3
from django.conf import settings
from django.http import JsonResponse, Http404, StreamingHttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Gallery, Photo, Flag, Comment, ZipDownload
from .tasks import build_zip
from . import nextcloud, object_storage


@ensure_csrf_cookie
def view_gallery(request, token):
    """GET /g/{token} - Render gallery HTML view."""
    try:
        gallery = Gallery.objects.prefetch_related(
            'photos__flags',
            'photos__comments',
        ).get(token=token, is_active=True)
    except Gallery.DoesNotExist:
        raise Http404("Gallery not found")

    photos = sorted(gallery.photos.all(), key=lambda p: p.display_order)

    photo_data = []
    for photo in photos:
        active_flags = [f.color for f in photo.flags.all()]
        photo_data.append({
            'id': photo.id,
            'filename': photo.filename,
            'thumbnail_url': photo.thumbnail_url,
            'preview_url': photo.preview_url,
            'flags': active_flags,
            'is_edited': photo.is_edited,
        })

    return render(request, 'gallery.html', {
        'gallery': gallery,
        'photos': photo_data,
    })


@require_http_methods(['POST'])
def toggle_flag(request, token, photo_id):
    """POST /g/{token}/photos/{photo_id}/flag?color=1 - Toggle a flag on a photo."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery)

    try:
        color = int(request.GET.get('color', 0))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid color'}, status=400)

    if color not in range(6):
        return JsonResponse({'error': 'Color must be 0-5'}, status=400)

    try:
        flag = Flag.objects.get(photo=photo, color=color)
        flag.delete()
        return JsonResponse({'color': color, 'active': False})
    except Flag.DoesNotExist:
        Flag.objects.create(photo=photo, color=color)
        return JsonResponse({'color': color, 'active': True})


@require_http_methods(['POST'])
def add_comment(request, token, photo_id):
    """POST /g/{token}/photos/{photo_id}/comment - Add a comment."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery)

    try:
        data = json.loads(request.body)
        body = nh3.clean(data.get('body', '').strip())
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not body or len(body) > 2000:
        return JsonResponse({'error': 'Body must be 1-2000 characters'}, status=400)

    comment = Comment.objects.create(photo=photo, body=body)

    return JsonResponse({
        'id': comment.id,
        'body': comment.body,
        'created_at': comment.created_at.isoformat(),
    })


@require_http_methods(['GET'])
def get_comments(request, token, photo_id):
    """GET /g/{token}/photos/{photo_id}/comments - Get comments for a photo."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery)
    comments = [
        {'id': c.id, 'body': c.body, 'created_at': c.created_at.isoformat()}
        for c in photo.comments.order_by('created_at')
    ]
    return JsonResponse(comments, safe=False)


@require_http_methods(['GET'])
def download_photo(request, token, photo_id):
    """GET /g/{token}/photos/{photo_id}/download - Download a single photo."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery)

    stream = nextcloud.download_file_stream(photo.nextcloud_path, photo.filename)
    response = StreamingHttpResponse(stream, content_type='application/octet-stream')
    # RFC 5987 encoding for safe Content-Disposition with arbitrary filenames
    encoded_filename = quote(photo.filename, safe='')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    return response


@require_http_methods(['POST'])
def start_zip_download(request, token):
    """POST /g/{token}/download/start - Kick off a background zip build."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    photo_ids = data.get('photo_ids')  # None means all

    if photo_ids is None:
        photos = gallery.photos.all()
    else:
        photos = gallery.photos.filter(id__in=photo_ids)

    if not photos.exists():
        return JsonResponse({'error': 'No photos found'}, status=400)

    photo_id_list = list(photos.values_list('id', flat=True))

    dl = ZipDownload.objects.create(
        gallery=gallery,
        progress_total=len(photo_id_list),
    )

    build_zip.delay(str(dl.id), photo_id_list)

    return JsonResponse({'download_id': str(dl.id)})


@require_http_methods(['GET'])
def zip_download_progress(request, token, download_id):
    """GET /g/{token}/download/{download_id}/progress - Poll zip build progress."""
    dl = get_object_or_404(ZipDownload, id=download_id, gallery__token=token, gallery__is_active=True)
    return JsonResponse({
        'status': dl.status,
        'progress_current': dl.progress_current,
        'progress_total': dl.progress_total,
        'file_size': dl.file_size,
    })


@require_http_methods(['POST'])
def cancel_zip_download(request, token, download_id):
    """POST /g/{token}/download/{download_id}/cancel - Cancel a zip build."""
    dl = get_object_or_404(
        ZipDownload, id=download_id, gallery__token=token, gallery__is_active=True,
    )
    if dl.status in ('pending', 'processing') and dl.celery_task_id:
        from config.celery import app
        app.control.revoke(dl.celery_task_id, terminate=True)
    dl.status = 'failed'
    dl.error_message = 'Cancelled by user'
    dl.save(update_fields=['status', 'error_message'])
    return JsonResponse({'status': 'cancelled'})


@require_http_methods(['GET'])
def serve_zip_download(request, token, download_id):
    """GET /g/{token}/download/{download_id}/file - Redirect to presigned R2 URL."""
    dl = get_object_or_404(
        ZipDownload, id=download_id, gallery__token=token, gallery__is_active=True, status='completed',
    )

    if not dl.r2_key:
        return JsonResponse({'error': 'File expired'}, status=410)

    encoded_slug = quote(dl.gallery.slug, safe='')
    filename = f"{encoded_slug}_photos.zip"
    url = object_storage.get_storage_client().generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.OBJECT_STORAGE_BUCKET_NAME,
            'Key': dl.r2_key,
            'ResponseContentDisposition': f"attachment; filename*=UTF-8''{filename}",
            'ResponseContentType': 'application/zip',
        },
        ExpiresIn=3600,
    )
    return redirect(url)
