from django.db import models

from ..config import HARD_DELETE
from ..models import SafeDeleteModel
from .testcase import SafeDeleteForceTestCase


class HardDeleteModel(SafeDeleteModel):
    _safedelete_policy = HARD_DELETE


class SoftDeleteCustomPrimaryModel(SafeDeleteModel):
    custom_id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=20)


class SoftDeleteTestCase(SafeDeleteForceTestCase):

    def setUp(self):
        self.instance = HardDeleteModel.objects.create()
        self.soft_instance = SoftDeleteCustomPrimaryModel.objects.create(
            custom_id=42, value="foo"
        )

    def test_harddelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertHardDelete(self.instance, expected_output=(1, {self.instance._meta.label: 1}))

    def test_update_or_create_no_unique_field(self):
        HardDeleteModel.objects.update_or_create(id=1)
        obj, created = HardDeleteModel.objects.update_or_create(id=1)
        self.assertEqual(obj.id, 1)

    def test_update_or_create_on_primary_key(self):
        obj, created = SoftDeleteCustomPrimaryModel.objects.update_or_create(
            custom_id=42, defaults={"value": "bar"},
        )
        self.assertEqual(obj.custom_id, 42)
        self.assertEqual(SoftDeleteCustomPrimaryModel.objects.get(custom_id=42).value, "bar")
        self.assertFalse(created)

    def test_update_or_create_on_soft_deleted_primary_key(self):
        self.soft_instance.delete()
        obj, created = SoftDeleteCustomPrimaryModel.objects.update_or_create(
            custom_id=42, defaults={"value": "bar"},
        )
        self.assertEqual(obj.custom_id, 42)
        self.assertEqual(SoftDeleteCustomPrimaryModel.objects.get(custom_id=42).value, "bar")
        self.assertFalse(created)
