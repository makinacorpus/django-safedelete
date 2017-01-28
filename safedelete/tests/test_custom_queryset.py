from django.db import models

from ..managers import SafeDeleteManager, SafeDeleteQueryset
from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class CustomQuerySet(SafeDeleteQueryset):

    def green(self):
        return self.filter(
            color='green'
        )


class CustomManager(SafeDeleteManager):
    _queryset_class = CustomQuerySet

    def green(self):
        """Implemented here so ``green`` available as manager's method
        """
        return self.get_queryset().green()


choices = (
    ('red', "Red"),
    ('green', "Green"),
)


class CustomQuerySetModel(SafeDeleteMixin):
    color = models.CharField(
        max_length=5,
        choices=choices
    )

    objects = CustomManager()


class CustomQuerySetTestCase(SafeDeleteTestCase):

    def test_custom_queryset_original_behavior(self):
        """Test whether creating a custom queryset works as intended."""
        CustomQuerySetModel.objects.create(
            color=choices[0][0]
        )
        CustomQuerySetModel.objects.create(
            color=choices[1][0]
        )

        self.assertEqual(CustomQuerySetModel.objects.count(), 2)
        self.assertEqual(CustomQuerySetModel.objects.green().count(), 1)

    def test_custom_queryset_custom_method(self):
        """Test custom filters for deleted objects"""
        instance = CustomQuerySetModel.objects.create(color=choices[1][0])
        instance.delete()

        deleted_only = CustomQuerySetModel.objects.deleted_only()

        # ensure deleted instances available
        self.assertEqual(deleted_only.count(), 1)

        # and they can be custom filtered
        self.assertEqual(deleted_only.green().count(), 1)
