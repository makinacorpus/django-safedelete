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

    def get_queryset(self):
        queryset = CustomQuerySet(self.model, using=self._db)
        return queryset.filter(deleted__isnull=True)

    def green(self):
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
