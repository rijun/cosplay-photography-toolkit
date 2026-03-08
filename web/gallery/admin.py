from django.contrib import admin

from .models import Gallery, Photo, Flag, Comment, FLAG_COLORS


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at', 'photo_count', 'flag_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['token', 'created_at']

    @admin.display(description='Photos')
    def photo_count(self, obj):
        return obj.photos.count()

    @admin.display(description='Flags')
    def flag_count(self, obj):
        return Flag.objects.filter(photo__gallery=obj).count()


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['filename', 'gallery', 'display_order', 'active_flags', 'comment_count']
    list_filter = ['gallery']
    search_fields = ['filename']

    @admin.display(description='Flags')
    def active_flags(self, obj):
        colors = dict(FLAG_COLORS)
        return ', '.join(colors[f.color] for f in obj.flags.all()) or '-'

    @admin.display(description='Comments')
    def comment_count(self, obj):
        return obj.comments.count()


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ['photo', 'get_color_display', 'created_at']
    list_filter = ['color', 'photo__gallery', 'created_at']
    readonly_fields = ['photo', 'created_at']

    @admin.display(description='Color')
    def get_color_display(self, obj):
        return dict(FLAG_COLORS).get(obj.color, str(obj.color))


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['photo', 'body_preview', 'created_at']
    list_filter = ['photo__gallery', 'created_at']
    readonly_fields = ['photo', 'created_at']

    @admin.display(description='Comment')
    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body