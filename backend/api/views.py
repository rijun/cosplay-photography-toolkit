import secrets

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from gallery.models import Gallery, GalleryMembership, Photo

from .authentication import ApiKeyAuthentication, RequireApiKey
from .serializers import (
    GalleryCreateSerializer,
    GalleryOutSerializer,
    PhotoOutSerializer,
    PhotoRegisterSerializer,
)


@api_view(['GET', 'POST', 'DELETE'])
@authentication_classes([ApiKeyAuthentication])
@permission_classes([RequireApiKey])
def galleries_view(request):
    """GET /api/galleries - List all galleries.
    POST /api/galleries - Create a new gallery.
    DELETE /api/galleries/{slug} - Delete a gallery.
    """
    if request.method == 'POST':
        serializer = GalleryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gallery = Gallery(
            name=serializer.validated_data['name'],
            slug=serializer.validated_data['slug'],
            cosplayer=serializer.validated_data.get('cosplayer', ''),
            token=secrets.token_urlsafe(24),
        )

        try:
            gallery.save()
        except IntegrityError:
            return Response(
                {'detail': 'Gallery with this slug already exists'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(GalleryOutSerializer(gallery).data, status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        gallery_slug = request.query_params.get('slug')
        if not gallery_slug:
            return Response({'detail': 'slug required'}, status=status.HTTP_400_BAD_REQUEST)

        if not Gallery.objects.filter(slug=gallery_slug).exists():
            return Response(
                {'detail': 'Gallery with this slug does not exist'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        gallery = Gallery.objects.get(slug=gallery_slug)

        try:
            with transaction.atomic():
                photo_ids = list(
                    GalleryMembership.objects.filter(gallery=gallery).values_list('photo_id', flat=True)
                )
                gallery.delete()
                orphans = Photo.objects.filter(id__in=photo_ids, galleries__isnull=True)
                # Report only the keys of photos no sibling gallery still uses. A group
                # photo shared with another gallery is not an orphan, so its objects stay.
                deleted_object_keys = [
                    key
                    for keys in orphans.values_list('thumbnail_key', 'preview_key')
                    for key in keys
                    if key
                ]
                orphans.delete()
        except Exception:
            return Response(
                {'detail': 'Gallery with this slug could not be deleted'},
                status=status.HTTP_409_CONFLICT,
            )

        data = GalleryOutSerializer(gallery).data
        data['deleted_object_keys'] = deleted_object_keys
        return Response(data, status=status.HTTP_200_OK)

    # GET
    galleries = Gallery.objects.order_by('-created_at')
    return Response(GalleryOutSerializer(galleries, many=True).data)


@api_view(['POST', 'DELETE'])
@authentication_classes([ApiKeyAuthentication])
@permission_classes([RequireApiKey])
def register_photo(request, slug):
    """POST /api/galleries/{slug}/photos - Register a photo.
    DELETE /api/galleries/{slug}/photos - Delete all photos in gallery.
    """
    try:
        gallery = Gallery.objects.get(slug=slug)
    except Gallery.DoesNotExist:
        return Response({'detail': 'Gallery not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        with transaction.atomic():
            photo_ids = list(
                GalleryMembership.objects.filter(gallery=gallery).values_list('photo_id', flat=True)
            )
            count, _ = GalleryMembership.objects.filter(gallery=gallery).delete()
            # Drop physical photos that no longer belong to any gallery; a photo
            # still shared with a sibling gallery keeps its flags and comments.
            Photo.objects.filter(id__in=photo_ids, galleries__isnull=True).delete()
        return Response({'deleted': count})

    serializer = PhotoRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Physical-photo identity is the R2 key pair: a group photo registered from
    # each cosplayer's gallery resolves to one Photo with several memberships.
    # update_or_create (not get_or_create) keeps refreshing nextcloud_path.
    with transaction.atomic():
        photo, _ = Photo.objects.update_or_create(
            thumbnail_key=serializer.validated_data['thumbnail_key'],
            preview_key=serializer.validated_data['preview_key'],
            defaults={
                'filename': serializer.validated_data['filename'],
                'nextcloud_path': serializer.validated_data['nextcloud_path'],
                'is_edited': serializer.validated_data.get('is_edited', False),
            },
        )
        _, created = GalleryMembership.objects.update_or_create(
            gallery=gallery,
            photo=photo,
            defaults={'display_order': serializer.validated_data['display_order']},
        )

    resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(PhotoOutSerializer(photo).data, status=resp_status)


@api_view(['GET'])
@authentication_classes([ApiKeyAuthentication])
@permission_classes([RequireApiKey])
def get_selections(request, slug):
    """GET /api/galleries/{slug}/selections?flag=0 - Get flagged photo filenames.

    Query params:
        flag: Color index (0=final, 1-5=person flags). Defaults to 0.
    """
    try:
        color = int(request.query_params.get('flag', 0))
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid flag value'}, status=status.HTTP_400_BAD_REQUEST)

    if color not in range(6):
        return Response({'detail': 'Flag must be 0-5'}, status=status.HTTP_400_BAD_REQUEST)

    filenames = (
        GalleryMembership.objects
        .filter(gallery__slug=slug, photo__flags__color=color)
        .order_by('display_order')
        .values_list('photo__filename', flat=True)
    )

    return Response(list(filenames))


@api_view(['PATCH'])
@authentication_classes([ApiKeyAuthentication])
@permission_classes([RequireApiKey])
def archive_gallery(request, slug):
    """PATCH /api/galleries/{slug}/archive - Archive a gallery (set is_active=False)."""
    try:
        gallery = Gallery.objects.get(slug=slug)
    except Gallery.DoesNotExist:
        return Response({'detail': 'Gallery not found'}, status=status.HTTP_404_NOT_FOUND)

    gallery.is_active = False
    gallery.save()

    return Response(GalleryOutSerializer(gallery).data)
