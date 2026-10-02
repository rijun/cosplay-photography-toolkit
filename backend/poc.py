from django.http import Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from gallery.models import Gallery, GalleryMembership

@ensure_csrf_cookie
def poc_gallery(request, token):
    """GET /g/{token} - Render gallery HTML view."""
    try:
        gallery = Gallery.objects.get(token=token, is_active=True)
    except Gallery.DoesNotExist:
        raise Http404("Gallery not found") from None

    # Query the through model directly: ordering via `photos.order_by(
    # 'memberships__display_order')` would add a second, unscoped join and
    # return duplicate/misordered rows for photos shared with other galleries.
    memberships = (
        GalleryMembership.objects
        .filter(gallery=gallery)
        .order_by('display_order')
        .select_related('photo')
        .prefetch_related('photo__flags')
    )

    photo_data = []
    for membership in memberships:
        photo = membership.photo
        photo_data.append({
            'id': photo.id,
            'filename': photo.filename,
            'thumbnail_url': photo.thumbnail_url,
            'preview_url': photo.preview_url,
            'flags': [f.color for f in photo.flags.all()],
            'is_edited': photo.is_edited,
        })

    return render(request, 'poc.html', {
        'gallery': gallery,
        'photos': photo_data,
    })
