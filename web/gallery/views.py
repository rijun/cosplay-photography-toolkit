import json

import nh3
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Gallery, Photo, Flag, Comment
from . import nextcloud


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

    data = nextcloud.download_file(photo.nextcloud_path, photo.filename)
    response = HttpResponse(data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{photo.filename}"'
    return response
