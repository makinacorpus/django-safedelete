try:
    from unittest import mock
except ImportError:
    import mock

from django.core.exceptions import ValidationError
from django.db import models

from ..models import SafeDeleteMixin
from .testcase import SafeDeleteForceTestCase


class SoftDeleteModel(SafeDeleteMixin):
    # SafeDeleteMixin has the soft delete policy by default
    pass


class UniqueSoftDeleteModel(SafeDeleteMixin):

    name = models.CharField(
        max_length=100,
        unique=True
    )


class SoftDeleteTestCase(SafeDeleteForceTestCase):

    def setUp(self):
        self.instance = SoftDeleteModel.objects.create()

    def test_softdelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertSoftDelete(self.instance)

    @mock.patch('safedelete.models.post_undelete.send')
    @mock.patch('safedelete.models.post_softdelete.send')
    def test_signals(self, mock_softdelete, mock_undelete):
        """The soft delete and undelete signals should be sent correctly for soft deleted models."""
        self.instance.delete()

        # Soft deleting the model should've sent a post_softdelete signal.
        self.assertEqual(
            mock_softdelete.call_count,
            1
        )

        # Saving makes it undelete the model.
        # Undeleting a model should call the post_undelete signal.
        self.instance.save()
        self.assertEqual(
            mock_undelete.call_count,
            1
        )

    def test_undelete(self):
        """Undeleting a soft deleted model should uhhh... undelete it?"""
        self.assertSoftDelete(self.instance, save=False)
        self.instance.undelete()
        self.assertEqual(
            SoftDeleteModel.objects.count(),
            1
        )
        self.assertEqual(
            SoftDeleteModel.objects.all_with_deleted().count(),
            1
        )

    def test_undelete_queryset(self):
        self.assertEqual(SoftDeleteModel.objects.count(), 1)

        SoftDeleteModel.objects.all().delete()
        self.assertEqual(SoftDeleteModel.objects.count(), 0)

        SoftDeleteModel.objects.all().undelete()  # Nonsense
        self.assertEqual(SoftDeleteModel.objects.count(), 0)

        SoftDeleteModel.objects.deleted_only().undelete()
        self.assertEqual(SoftDeleteModel.objects.count(), 1)

    def test_validate_unique(self):
        """Check that uniqueness is also checked against deleted objects """
        UniqueSoftDeleteModel.objects.create(
            name='test'
        ).delete()
        self.assertRaises(
            ValidationError,
            UniqueSoftDeleteModel(
                name='test'
            ).validate_unique
        )
