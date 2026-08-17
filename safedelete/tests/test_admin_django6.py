"""Tests for upstream issue #247 - Django 6 admin ``log_action`` removal.

Django 6 removed ``LogEntry.objects.log_action(...)`` in favour of
``log_actions(user_id, queryset, action_flag, change_message="", *,
single_object=False)``. The fork's :meth:`SafeDeleteAdmin.log_undeletion`
dispatches by Django version so the helper works on both <= 5.x and >= 6.x.

Issue: https://github.com/makinacorpus/django-safedelete/issues/247
"""

import django
from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import RequestFactory, TestCase

from ..admin import SafeDeleteAdmin
from ..config import SOFT_DELETE
from ..models import SafeDeleteModel


class AdminLoggableCategory(SafeDeleteModel):
    """Dedicated safedelete model so tests never share state."""

    _safedelete_policy = SOFT_DELETE

    name = models.CharField(max_length=64, default="")

    def __str__(self):
        return self.name


class LogUndeletionTestCase(TestCase):
    """Regression guard for :meth:`SafeDeleteAdmin.log_undeletion`."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="admin", email="a@example.com", password="x"
        )
        self.factory = RequestFactory()

    def test_log_undeletion_creates_change_log_entry(self):
        """log_undeletion must produce a single CHANGE LogEntry."""
        cat = AdminLoggableCategory.objects.create(name="toundelete")
        cat.delete(force_policy=SOFT_DELETE)

        request = self.factory.get("/admin/")
        request.user = self.user

        model_admin = SafeDeleteAdmin(AdminLoggableCategory, admin.site)
        # The call must not raise - in particular it must not hit the
        # removed ``log_action`` helper on Django >= 6.
        model_admin.log_undeletion(request, cat, str(cat))

        entry = LogEntry.objects.filter(
            user=self.user,
            content_type=ContentType.objects.get_for_model(AdminLoggableCategory),
            object_id=str(cat.pk),
        ).first()
        self.assertIsNotNone(entry, "admin log entry must be written")
        self.assertEqual(entry.action_flag, CHANGE)
        self.assertNotEqual(entry.action_flag, ADDITION)

    def test_log_undeletion_uses_version_specific_api(self):
        """The dispatcher picks the API that matches the installed Django.

        On Django >= 6, ``log_actions`` is the only available entry point;
        on Django <= 5.x, ``log_action`` must still be used so the fork
        remains drop-in for users on older Django versions.
        """
        cat = AdminLoggableCategory.objects.create(name="dispatch")
        cat.delete(force_policy=SOFT_DELETE)

        request = self.factory.get("/admin/")
        request.user = self.user

        model_admin = SafeDeleteAdmin(AdminLoggableCategory, admin.site)
        model_admin.log_undeletion(request, cat, str(cat))

        self.assertEqual(LogEntry.objects.count(), 1)
        # Smoke-check the manager still carries the version-appropriate
        # helpers - detecting an accidental removal in future Django
        # releases quickly.
        if django.VERSION[0] >= 6:
            self.assertTrue(hasattr(LogEntry.objects, "log_actions"))
        else:  # pragma: no cover - executed on Django <= 5.x only
            self.assertTrue(hasattr(LogEntry.objects, "log_action"))
