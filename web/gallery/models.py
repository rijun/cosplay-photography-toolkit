from django.db import models

from gallery import object_storage


class Gallery(models.Model):
    name = models.TextField()
    slug = models.TextField(unique=True)
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "galleries"


class Photo(models.Model):
    gallery = models.ForeignKey(
        Gallery, on_delete=models.CASCADE, related_name="photos"
    )
    filename = models.TextField()
    object_key = models.TextField()
    thumbnail_key = models.TextField()
    preview_key = models.TextField()
    display_order = models.IntegerField(default=0)
    is_edited = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def object_url(self):
        return object_storage.photo_url(self.object_key)

    @property
    def thumbnail_url(self):
        return object_storage.photo_url(self.thumbnail_key)

    @property
    def preview_url(self):
        return object_storage.photo_url(self.preview_key)

    class Meta:
        db_table = "photos"


FLAG_COLORS = [
    (0, "final"),
    (1, "rose"),
    (2, "lavender"),
    (3, "sage"),
    (4, "sky"),
    (5, "amber"),
]


class Flag(models.Model):
    photo = models.ForeignKey(
        Photo, on_delete=models.CASCADE, related_name="flags"
    )
    color = models.IntegerField(choices=FLAG_COLORS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "flags"
        unique_together = ("photo", "color")


class Comment(models.Model):
    photo = models.ForeignKey(
        Photo, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments"
