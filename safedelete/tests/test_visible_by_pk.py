from django.db import models

from ..config import DELETED_VISIBLE_BY_PK
from ..managers import SafeDeleteManager
from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class PkVisibleManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_PK


class PkVisibleModel(SafeDeleteMixin):

    objects = PkVisibleManager()

    name = models.CharField(
        max_length=100
    )


class VisibilityTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = PkVisibleModel.objects.create(
            name='instance'
        )

    def test_visible_by_pk(self):
        """Test whether the soft deleted model can be found by filtering on pk."""
        self.assertSoftDelete(self.instance, save=False)
        self.assertEqual(
            PkVisibleModel.objects.filter(
                pk=self.instance.pk
            ).count(),
            1
        )
        # Raises PkVisibleModel.DoesNotExist if it isn't found
        PkVisibleModel.objects.get(
            pk=self.instance.pk
        )

    def test_invisible_by_name(self):
        """Test whether the soft deleted model cannot be found by filtering on name."""
        self.assertSoftDelete(self.instance, save=False)
        self.assertEqual(
            PkVisibleModel.objects.filter(
                name=self.instance.name
            ).count(),
            0
        )
        self.assertRaises(
            PkVisibleModel.DoesNotExist,
            PkVisibleModel.objects.get,
            name=self.instance.name
        )
