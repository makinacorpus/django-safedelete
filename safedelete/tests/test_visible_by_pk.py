from django.db import models

from ..config import DELETED_VISIBLE_BY_FIELD
from ..managers import SafeDeleteManager
from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class PkVisibleManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_FIELD


class PkVisibleModel(SafeDeleteModel):

    objects = PkVisibleManager()

    name = models.CharField(
        max_length=100
    )


class NameVisibleManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_FIELD
    _safedelete_visibility_field = 'name'


class NameVisibleField(SafeDeleteModel):
    name = models.CharField(max_length=200, unique=True)

    objects = NameVisibleManager()

    def __str__(self):
        return self.name


class VisibilityTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = PkVisibleModel.objects.create(
            name='instance'
        )
        self.namevisiblefield = (
            NameVisibleField.objects.create(name='NVF 1'),
            NameVisibleField.objects.create(name='NVF 2'),
            NameVisibleField.objects.create(name='NVF 3'),
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

    def test_access_by_passed_visible_field(self):
        """ Test wether the namefield model can be found by filtering on name. """
        name = self.namevisiblefield[0].name
        self.namevisiblefield[0].delete()
        self.assertRaises(
            NameVisibleField.DoesNotExist,
            NameVisibleField.objects.get,
            pk=self.namevisiblefield[0].id
        )
        self.assertEqual(self.namevisiblefield[0], NameVisibleField.objects.get(name=name))
        cat = NameVisibleField.objects.filter(name=name)
        self.assertEqual(len(cat), 1)
        self.assertEqual(self.namevisiblefield[0], cat[0])
