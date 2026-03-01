import json

import nh3
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Gallery, Photo, Selection, Comment
from .object_storage import photo_url


@ensure_csrf_cookie
def view_gallery(request, token):
    """GET /g/{token} - Render gallery HTML view."""
    try:
        gallery = Gallery.objects.prefetch_related(
            'photos__selection',
            'photos__comments',
        ).get(token=token)
    except Gallery.DoesNotExist:
        raise Http404("Gallery not found")

    photos = sorted(gallery.photos.all(), key=lambda p: p.display_order)

    photo_data = []
    for photo in photos:
        is_selected = hasattr(photo, 'selection')

        photo_data.append({
            'id': photo.id,
            'filename': photo.filename,
            'url': photo_url(photo.object_key),
            'is_selected': is_selected,
            'comments': [
                {
                    'id': c.id,
                    'body': c.body,
                    'created_at': c.created_at.isoformat(),
                }
                for c in sorted(photo.comments.all(), key=lambda c: c.created_at)
            ],
        })

    return render(request, 'gallery.html', {
        'gallery': gallery,
        'photos': photo_data,
        'photos_json': json.dumps(photo_data),
    })


@require_http_methods(['POST'])
def toggle_selection(request, token, photo_id):
    """POST /g/{token}/photos/{photo_id}/select - Toggle photo selection."""
    gallery = get_object_or_404(Gallery, token=token)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery)

    try:
        selection = Selection.objects.get(photo=photo)
        selection.delete()
        return JsonResponse({'selected': False})
    except Selection.DoesNotExist:
        Selection.objects.create(photo=photo)
        return JsonResponse({'selected': True})


@require_http_methods(['POST'])
def add_comment(request, token, photo_id):
    """POST /g/{token}/photos/{photo_id}/comment - Add a comment."""
    gallery = get_object_or_404(Gallery, token=token)
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
