from django.db import migrations


def populate(apps, schema_editor):
    Photo = apps.get_model("gallery", "Photo")
    Comment = apps.get_model("gallery", "Comment")
    Gallery = apps.get_model("gallery", "Gallery")
    GalleryMembership = apps.get_model("gallery", "GalleryMembership")

    GalleryMembership.objects.bulk_create(
        [
            GalleryMembership(
                gallery_id=photo.gallery_id,
                photo_id=photo.id,
                display_order=photo.display_order,
            )
            for photo in Photo.objects.all().iterator()
        ],
        ignore_conflicts=True,
    )

    for comment in Comment.objects.select_related("photo").iterator():
        comment.gallery_id = comment.photo.gallery_id
        comment.save(update_fields=["gallery"])

    # Best-effort cosplayer label. Convention galleries are named
    # "{convention} – {day} – {cosplayer}" (en-dash, cli/commands/upload.py);
    # shoot galleries are "{date} {character}".
    for gallery in Gallery.objects.all().iterator():
        if "–" in gallery.name:
            gallery.cosplayer = gallery.name.rsplit("–", 1)[-1].strip()
        elif " " in gallery.name:
            gallery.cosplayer = gallery.name.split(" ", 1)[1].strip()
        else:
            continue
        gallery.save(update_fields=["cosplayer"])


def unpopulate(apps, schema_editor):
    GalleryMembership = apps.get_model("gallery", "GalleryMembership")
    GalleryMembership.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("gallery", "0015_shared_photo_schema")]

    operations = [migrations.RunPython(populate, unpopulate)]
