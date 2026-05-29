from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import FLAG_COLORS, Comment, Flag, Gallery, Photo


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'url', 'created_at', 'photo_count', 'flag_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['slug', 'token', 'url', 'created_at', 'flag_list']

    @admin.display(description='URL')
    def url(self, obj):
        url = f'/g/{obj.token}'
        return format_html('<a href="{}">{}</a>', url, url)

    @admin.display(description='Photos')
    def photo_count(self, obj):
        return obj.photos.count()

    @admin.display(description='Flags')
    def flag_count(self, obj):
        return Flag.objects.filter(photo__gallery=obj).count()

    @admin.display(description='Selections')
    def flag_list(self, obj):
        if not obj.pk:
            return '-'
        flags = (
            Flag.objects
            .filter(photo__gallery=obj)
            .select_related('photo')
            .order_by('color', 'photo__filename')
        )
        if not flags:
            return format_html('<em>No selections yet</em>')

        color_names = dict(FLAG_COLORS)
        grouped: dict[int, list[str]] = {flag.color: [] for flag in flags}
        for flag in flags:
            grouped[flag.color].append(flag.photo.filename)

        rows = format_html_join(
            '', '<tr><td>{}</td><td>{}</td></tr>',
            ((color_names[color], ', '.join(filenames)) for color, filenames in grouped.items()),
        )
        return format_html('<table>{}</table>', rows)


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