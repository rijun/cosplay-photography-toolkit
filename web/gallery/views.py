import io
import json
import re
import zipfile
from pathlib import Path

import nh3
from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .object_storage import get_storage_client

from .models import Gallery, Photo, Flag, Comment


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
def download_photos(request, token):
    """GET /g/{token}/download[?ids=1,2,3] - Download photos as a streaming zip."""
    gallery = get_object_or_404(Gallery, token=token, is_active=True)

    photos = gallery.photos.order_by('display_order')
    ids_param = request.GET.get('ids', '').strip()
    if ids_param:
        ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        photos = photos.filter(id__in=ids)

    photos = list(photos)
    if not photos:
        return HttpResponse('No photos found', status=404)

    safe_slug = re.sub(r'[^\w\-]', '_', gallery.slug)

    response = StreamingHttpResponse(
        _zip_stream(photos),
        content_type='application/zip',
    )
    response['Content-Disposition'] = f'attachment; filename="{safe_slug}_photos.zip"'
    return response


def _zip_stream(photos):
    """Yield zip file contents, one photo at a time in memory."""
    client = get_storage_client()
    bucket = settings.OBJECT_STORAGE_BUCKET_NAME

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED, allowZip64=True) as zf:
        for photo in photos:
            obj = client.get_object(Bucket=bucket, Key=photo.object_key)
            zf.writestr(photo.filename, obj['Body'].read())
            # Flush what's been written so far
            buf.seek(0)
            yield buf.read()
            # Reset buffer but keep the ZipFile state
            buf.seek(0)
            buf.truncate()

    # Yield the central directory (written when ZipFile closes)
    buf.seek(0)
    yield buf.read()
