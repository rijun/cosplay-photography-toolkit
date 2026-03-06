from django.db import models


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
    display_order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "photos"


class Selection(models.Model):
    photo = models.OneToOneField(
        Photo, on_delete=models.CASCADE, related_name="selection"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "selections"


class Comment(models.Model):
    photo = models.ForeignKey(
        Photo, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments"
