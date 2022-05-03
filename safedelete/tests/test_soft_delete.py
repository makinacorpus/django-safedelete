try:
    from unittest import mock
except ImportError:
    import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.test import override_settings

from ..config import SOFT_DELETE_CASCADE
from ..models import SafeDeleteModel
from .testcase import SafeDeleteForceTestCase


class SoftDeleteModel(SafeDeleteModel):
    # SafeDeleteModel has the soft delete policy by default
    pass


class SoftDeleteRelatedModel(SafeDeleteModel):
    related = models.ForeignKey(SoftDeleteModel, on_delete=models.CASCADE)


class SoftDeleteMixinModel(SafeDeleteModel):
    # Legacy compatibility with the older SafeDeleteModel name.
    pass


class UniqueSoftDeleteModel(SafeDeleteModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )


class UniqueConstraintSoftDeleteModel(SafeDeleteModel):

    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "team"],
                name="unique_constraint",
            )
        ]


class UniqueTogetherSoftDeleteModel(SoftDeleteModel):

    name = models.CharField(max_length=100)
    team = models.CharField(max_length=100)

    class Meta:
        unique_together = ("name", "team")


class SoftDeleteTestCase(SafeDeleteForceTestCase):

    def setUp(self):
        self.instance = SoftDeleteModel.objects.create()

    def test_softdelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertSoftDelete(self.instance, expected_output=(1, {self.instance._meta.label: 1}))

    def test_softdelete_mixin(self):
        """Deprecated: Deleting a SafeDeleteModel model with the soft delete policy should only mask it, not delete it."""
        self.assertSoftDelete(SoftDeleteMixinModel.objects.create())

    @mock.patch('safedelete.models.post_undelete.send')
    @mock.patch('safedelete.models.post_softdelete.send')
    @mock.patch('safedelete.models.pre_softdelete.send')
    def test_signals(self, mock_presoftdelete, mock_softdelete, mock_undelete):
        """The soft delete and undelete signals should be sent correctly for soft deleted models."""
        self.instance.delete()

        # Soft deleting the model should've sent a pre_softdelete and a post_softdelete signals.
        self.assertEqual(
            mock_presoftdelete.call_count,
            1
        )

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
            SoftDeleteModel.all_objects.count(),
            1
        )

    def test_undelete_queryset(self):
        self.assertEqual(SoftDeleteModel.objects.count(), 1)

        SoftDeleteModel.objects.all().delete()
        self.assertEqual(SoftDeleteModel.objects.count(), 0)

        SoftDeleteModel.objects.all().undelete()  # Nonsense
        self.assertEqual(SoftDeleteModel.objects.count(), 0)

        SoftDeleteModel.deleted_objects.all().undelete()
        self.assertEqual(SoftDeleteModel.objects.count(), 1)

    def test_undelete_with_soft_delete_policy_and_forced_soft_delete_cascade_policy(self):
        self.assertEqual(SoftDeleteModel.objects.count(), 1)
        SoftDeleteRelatedModel.objects.create(related=SoftDeleteModel.objects.first())
        self.assertEqual(SoftDeleteRelatedModel.objects.count(), 1)

        SoftDeleteModel.objects.all().delete()
        self.assertEqual(SoftDeleteModel.objects.count(), 0)

        SoftDeleteRelatedModel.objects.all().delete()
        self.assertEqual(SoftDeleteRelatedModel.objects.count(), 0)

        SoftDeleteModel.deleted_objects.all().undelete(force_policy=SOFT_DELETE_CASCADE)
        self.assertEqual(SoftDeleteModel.objects.count(), 1)
        self.assertEqual(SoftDeleteRelatedModel.objects.count(), 0)

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

    def test_update_or_create_no_unique_field(self):
        SoftDeleteModel.objects.update_or_create(id=1)
        obj, created = SoftDeleteModel.objects.update_or_create(id=1)
        self.assertEqual(obj.id, 1)

    def test_update_or_create_with_unique_field(self):
        # Create and soft-delete object
        obj, created = UniqueSoftDeleteModel.objects.update_or_create(name='unique-test')
        obj.delete()
        # Update it and see if it fails
        obj, created = UniqueSoftDeleteModel.objects.update_or_create(name='unique-test')
        self.assertEqual(obj.name, 'unique-test')
        self.assertEqual(created, False)

    def test_update_or_create_with_unique_constraint(self):
        # Create and soft-delete object
        obj, created = UniqueConstraintSoftDeleteModel.objects.update_or_create(name='thor', team='avengers')
        obj.delete()
        # Update it and see if it fails
        obj, created = UniqueConstraintSoftDeleteModel.objects.update_or_create(name='thor', team='avengers', defaults={})
        self.assertEqual(obj.name, 'thor')
        self.assertEqual(obj.team, 'avengers')
        self.assertFalse(created)

    def test_update_or_create_with_unique_together_constraint(self):
        # Create and soft-delete object
        obj, created = UniqueTogetherSoftDeleteModel.objects.update_or_create(name='thor', team='avengers')
        obj.delete()
        # Update it and see if it fails
        obj, created = UniqueTogetherSoftDeleteModel.objects.update_or_create(name='thor', team='avengers')
        self.assertEqual(obj.name, 'thor')
        self.assertEqual(obj.team, 'avengers')
        self.assertFalse(created)

    def test_model_has_unique_fields(self):
        self.assertFalse(SoftDeleteModel.has_unique_fields())
        self.assertTrue(UniqueSoftDeleteModel.has_unique_fields())
        self.assertTrue(UniqueTogetherSoftDeleteModel.has_unique_fields())
        self.assertTrue(UniqueConstraintSoftDeleteModel.has_unique_fields())

    @override_settings(SAFE_DELETE_INTERPRET_UNDELETED_OBJECTS_AS_CREATED=True)
    def test_update_or_create_flag_with_settings_flag_active(self):
        # Create and soft-delete object
        obj, created = UniqueSoftDeleteModel.objects.update_or_create(name='unique-test')
        obj.delete()
        # Update it and see if it fails
        obj, created = UniqueSoftDeleteModel.objects.update_or_create(name='unique-test')
        self.assertEqual(obj.name, 'unique-test')
        # Settings flag is active so the revived object should be interpreted as created
        self.assertEqual(created, True)
