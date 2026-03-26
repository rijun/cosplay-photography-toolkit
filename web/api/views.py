import secrets

from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
import nh3

from gallery.models import Gallery, Photo, Flag
from .authentication import ApiKeyAuthentication, RequireApiKey
from .serializers import (
    GalleryCreateSerializer,
    GalleryOutSerializer,
    PhotoRegisterSerializer,
    PhotoOutSerializer,
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
            gallery.delete()
        except Exception:
            return Response(
                {'detail': 'Gallery with this slug could not be deleted'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(GalleryOutSerializer(gallery).data, status=status.HTTP_200_OK)

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
        count, _ = gallery.photos.all().delete()
        return Response({'deleted': count})

    serializer = PhotoRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    photo, created = Photo.objects.update_or_create(
        gallery=gallery,
        filename=serializer.validated_data['filename'],
        is_edited=serializer.validated_data.get('is_edited', False),
        defaults={
            'nextcloud_path': serializer.validated_data['nextcloud_path'],
            'thumbnail_key': serializer.validated_data['thumbnail_key'],
            'preview_key': serializer.validated_data['preview_key'],
            'display_order': serializer.validated_data['display_order'],
        },
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

    filenames = Photo.objects.filter(
        gallery__slug=slug,
        flags__color=color,
    ).order_by('display_order').values_list('filename', flat=True)

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
