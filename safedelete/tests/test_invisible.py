from django.db import models

from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class InvisibleModel(SafeDeleteMixin):
    # SafeDeleteMixin subclasses automatically have their visibility set to invisible.

    name = models.CharField(
        max_length=100
    )


class VisibilityTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = InvisibleModel.objects.create(
            name='instance'
        )

    def test_visible_by_pk(self):
        """Test whether the soft deleted model cannot be found by filtering on pk."""
        self.assertSoftDelete(self.instance, save=False)
        self.assertEqual(
            InvisibleModel.objects.filter(
                pk=self.instance.pk
            ).count(),
            0
        )
        self.assertRaises(
            InvisibleModel.DoesNotExist,
            InvisibleModel.objects.get,
            pk=self.instance.pk
        )

    def test_invisible_by_name(self):
        """Test whether the soft deleted model cannot be found by filtering on name."""
        self.assertSoftDelete(self.instance, save=False)
        self.assertEqual(
            InvisibleModel.objects.filter(
                name=self.instance.name
            ).count(),
            0
        )
        self.assertRaises(
            InvisibleModel.DoesNotExist,
            InvisibleModel.objects.get,
            name=self.instance.name
        )
