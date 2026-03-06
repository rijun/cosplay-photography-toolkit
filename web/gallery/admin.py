from django.contrib import admin

from .models import Gallery, Photo, Selection, Comment


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at', 'photo_count', 'selection_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['token', 'created_at']

    @admin.display(description='Photos')
    def photo_count(self, obj):
        return obj.photos.count()

    @admin.display(description='Selections')
    def selection_count(self, obj):
        return Selection.objects.filter(photo__gallery=obj).count()


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['filename', 'gallery', 'display_order', 'is_selected', 'comment_count']
    list_filter = ['gallery']
    search_fields = ['filename']

    @admin.display(boolean=True, description='Selected')
    def is_selected(self, obj):
        return hasattr(obj, 'selection')

    @admin.display(description='Comments')
    def comment_count(self, obj):
        return obj.comments.count()


@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    list_display = ['photo', 'created_at']
    list_filter = ['photo__gallery', 'created_at']
    readonly_fields = ['photo', 'created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['photo', 'body_preview', 'created_at']
    list_filter = ['photo__gallery', 'created_at']
    readonly_fields = ['photo', 'created_at']

    @admin.display(description='Comment')
    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
