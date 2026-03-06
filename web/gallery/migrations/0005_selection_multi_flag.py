# Generated manually for multi-flag selection system

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_add_is_active_fix_selection_related_name'),
    ]

    operations = [
        # Step 1: Add flag field with default 'red' for existing data
        migrations.AddField(
            model_name='selection',
            name='flag',
            field=models.CharField(
                choices=[
                    ('red', 'Red'),
                    ('blue', 'Blue'),
                    ('green', 'Green'),
                    ('yellow', 'Yellow'),
                    ('purple', 'Purple'),
                ],
                default='red',
                max_length=10,
            ),
            preserve_default=False,
        ),
        # Step 2: Change OneToOneField to ForeignKey
        migrations.AlterField(
            model_name='selection',
            name='photo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='selections',
                to='gallery.photo',
            ),
        ),
        # Step 3: Add unique constraint for photo + flag combination
        migrations.AlterUniqueTogether(
            name='selection',
            unique_together={('photo', 'flag')},
        ),
    ]
