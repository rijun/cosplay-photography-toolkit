import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("gallery", "0017_dedupe_photos")]

    operations = [
        # Drop the old per-gallery constraint before the field it references.
        migrations.RemoveConstraint(
            model_name="photo",
            name="unique_photo_per_gallery",
        ),
        migrations.RemoveField(
            model_name="photo",
            name="gallery",
        ),
        migrations.RemoveField(
            model_name="photo",
            name="display_order",
        ),
        migrations.AddConstraint(
            model_name="photo",
            constraint=models.UniqueConstraint(
                fields=("thumbnail_key", "preview_key"),
                name="unique_physical_photo",
            ),
        ),
        # Every row was populated in 0016.
        migrations.AlterField(
            model_name="comment",
            name="gallery",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="gallery.gallery",
            ),
        ),
    ]
