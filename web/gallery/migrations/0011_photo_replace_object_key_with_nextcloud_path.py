from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0010_photo_is_edited'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='nextcloud_path',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='photo',
            name='object_key',
        ),
    ]
