"""Collapse per-gallery photo rows into one row per physical file.

Group photos were registered once per cosplayer gallery, all pointing at the
same R2 objects. Identity here is the (thumbnail_key, preview_key) pair, which
is why the convention R2 prefix must never include the cosplayer.
"""

from collections import defaultdict

from django.db import migrations, models


def _duplicate_groups(Photo):
    """Group photos by physical identity, keeping only groups with >1 row."""
    groups = defaultdict(list)
    for photo in Photo.objects.order_by("id").iterator():
        groups[(photo.thumbnail_key, photo.preview_key)].append(photo)
    return {keys: rows for keys, rows in groups.items() if len(rows) > 1}


def _validate_mergeable(Photo):
    """Raise if any photo cannot be safely deduplicated by its R2 keys."""
    blank = sorted(
        Photo.objects
        .filter(models.Q(thumbnail_key="") | models.Q(preview_key=""))
        .values_list("id", flat=True)
    )
    if blank:
        raise RuntimeError(
            "Photos with blank R2 keys cannot be deduplicated (they would all "
            f"collapse into one row). Fix these by hand first: {blank}"
        )

    problems = []
    for keys, rows in _duplicate_groups(Photo).items():
        variants = {(r.filename, r.nextcloud_path, r.is_edited) for r in rows}
        if len(variants) > 1:
            problems.append(f"{keys}: {sorted(variants)}")

    if problems:
        raise RuntimeError(
            "Photos share R2 keys but are not the same physical file — merging "
            "them would lose data. Resolve these by hand first:\n"
            + "\n".join(problems)
        )


def _merge_duplicates(Photo, Flag, Comment, GalleryMembership):
    """Collapse duplicate photo rows onto the oldest row. Returns rows deleted."""
    deleted = 0
    for rows in _duplicate_groups(Photo).values():
        survivor, duplicates = rows[0], rows[1:]

        seen_galleries = set(
            GalleryMembership.objects.filter(photo=survivor).values_list("gallery_id", flat=True)
        )
        seen_colors = set(Flag.objects.filter(photo=survivor).values_list("color", flat=True))

        for duplicate in duplicates:
            for membership in GalleryMembership.objects.filter(photo=duplicate):
                if membership.gallery_id in seen_galleries:
                    membership.delete()
                else:
                    membership.photo = survivor
                    membership.save(update_fields=["photo"])
                    seen_galleries.add(membership.gallery_id)

            for flag in Flag.objects.filter(photo=duplicate):
                if flag.color in seen_colors:
                    flag.delete()
                else:
                    flag.photo = survivor
                    flag.save(update_fields=["photo"])
                    seen_colors.add(flag.color)

            Comment.objects.filter(photo=duplicate).update(photo=survivor)

            duplicate.delete()
            deleted += 1

    return deleted


def dedupe(apps, schema_editor):
    Photo = apps.get_model("gallery", "Photo")
    Flag = apps.get_model("gallery", "Flag")
    Comment = apps.get_model("gallery", "Comment")
    GalleryMembership = apps.get_model("gallery", "GalleryMembership")

    _validate_mergeable(Photo)
    _merge_duplicates(Photo, Flag, Comment, GalleryMembership)


class Migration(migrations.Migration):
    dependencies = [("gallery", "0016_populate_memberships")]

    # Irreversible: merged rows cannot be split back apart.
    operations = [migrations.RunPython(dedupe, migrations.RunPython.noop)]
