"""Tests for upstream issue #242 - ``QuerySet.update()`` bypass.

Upstream bug: ``Model.objects.update(field=value)`` silently writes to
soft-deleted rows, because Django's bulk-update path never touches
``SafeDeleteQuery._filter_visibility()``.

This fork plugs the gap in :class:`safedelete.queryset.SafeDeleteQueryset`.

Issue: https://github.com/makinacorpus/django-safedelete/issues/242
"""

from django.db import models
from django.test import TestCase

from ..config import DELETED_VISIBLE, FIELD_NAME, SOFT_DELETE
from ..models import SafeDeleteModel


class UpdateBypassCategory(SafeDeleteModel):
    """Dedicated model so we do not share state with other suites."""

    _safedelete_policy = SOFT_DELETE

    name = models.CharField(max_length=64, default="")
    status = models.CharField(max_length=16, default="draft")


class UpdateBypassTestCase(TestCase):
    """Regression guard for the ``.update()`` visibility filter."""

    def test_update_on_alive_rows_works(self):
        """Sanity check: ``.update()`` still edits alive rows."""
        alive = UpdateBypassCategory.objects.create(name="a", status="draft")
        alive2 = UpdateBypassCategory.objects.create(name="b", status="draft")

        affected = UpdateBypassCategory.objects.update(status="published")

        alive.refresh_from_db()
        alive2.refresh_from_db()
        self.assertEqual(affected, 2)
        self.assertEqual(alive.status, "published")
        self.assertEqual(alive2.status, "published")

    def test_update_via_all_objects_skips_soft_deleted(self):
        """``all_objects.update(...)`` must NOT touch soft-deleted rows.

        This is the core #242 regression: upstream silently wrote to
        every row in the table, including the soft-deleted one.
        """
        alive = UpdateBypassCategory.objects.create(name="alive", status="draft")
        dead = UpdateBypassCategory.objects.create(name="dead", status="draft")
        dead.delete(force_policy=SOFT_DELETE)
        dead.refresh_from_db()
        self.assertIsNotNone(getattr(dead, FIELD_NAME))

        affected = UpdateBypassCategory.all_objects.update(status="published")

        alive.refresh_from_db()
        dead.refresh_from_db()
        self.assertEqual(alive.status, "published", "alive row must be updated")
        self.assertEqual(
            dead.status,
            "draft",
            "soft-deleted row MUST NOT be updated (Issue #242)",
        )
        self.assertEqual(
            affected, 1, "update() must report only the alive row as affected"
        )

    def test_update_via_default_manager_skips_soft_deleted(self):
        """``objects.update(...)`` keeps respecting the hidden-row filter."""
        alive = UpdateBypassCategory.objects.create(name="alive", status="draft")
        dead = UpdateBypassCategory.objects.create(name="dead", status="draft")
        dead.delete(force_policy=SOFT_DELETE)

        affected = UpdateBypassCategory.objects.update(status="published")

        alive.refresh_from_db()
        dead.refresh_from_db()
        self.assertEqual(affected, 1)
        self.assertEqual(alive.status, "published")
        self.assertEqual(dead.status, "draft")

    def test_update_with_force_visibility_deleted_visible_still_writes(self):
        """Explicit opt-in via ``force_visibility=DELETED_VISIBLE`` works."""
        alive = UpdateBypassCategory.objects.create(name="alive", status="draft")
        dead = UpdateBypassCategory.objects.create(name="dead", status="draft")
        dead.delete(force_policy=SOFT_DELETE)

        # Explicit opt-in: the caller declares they want to touch
        # soft-deleted rows too. The fork preserves that semantics.
        affected = (
            UpdateBypassCategory.all_objects.all(force_visibility=DELETED_VISIBLE)
            .update(status="published")
        )

        alive.refresh_from_db()
        dead.refresh_from_db()
        self.assertEqual(affected, 2)
        self.assertEqual(alive.status, "published")
        self.assertEqual(dead.status, "published")

    def test_deleted_objects_update_targets_soft_deleted(self):
        """``deleted_objects.update(...)`` targets soft-deleted rows only."""
        alive = UpdateBypassCategory.objects.create(name="alive", status="draft")
        dead = UpdateBypassCategory.objects.create(name="dead", status="draft")
        dead.delete(force_policy=SOFT_DELETE)

        affected = UpdateBypassCategory.deleted_objects.update(status="archived")

        alive.refresh_from_db()
        dead.refresh_from_db()
        self.assertEqual(affected, 1)
        self.assertEqual(alive.status, "draft")
        self.assertEqual(dead.status, "archived")
