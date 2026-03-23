from rest_framework import serializers

from gallery.models import Gallery, Photo


class GalleryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.RegexField(r'^[a-z0-9._\-]+$', max_length=80)


class GalleryOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['id', 'name', 'slug', 'token', 'created_at', 'is_active']


class PhotoRegisterSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    object_key = serializers.CharField(max_length=255)
    thumbnail_key = serializers.CharField(max_length=255)
    preview_key = serializers.CharField(max_length=255)
    display_order = serializers.IntegerField(default=0)
    is_edited = serializers.BooleanField(default=False)


class PhotoOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'filename', 'object_key', 'thumbnail_key', 'preview_key', 'display_order', 'is_edited', 'uploaded_at']
