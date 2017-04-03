import unittest

from django.test import TestCase

from ..config import HARD_DELETE, SOFT_DELETE


class SafeDeleteTestCase(TestCase):

    def assertDelete(self, instance, expected_results, force_policy=None, save=True):
        """Assert specific specific expected results before delete, after delete and after save.

        Example of expected_results, see SafeDeleteTestCase.assertSoftDelete.

        Args:
            instance: Model instance.
            expected_results: Specific expected results before delete, after delete and after save.
            force_policy: Specific policy to force, None if no policy forced. (default: {None})
            save: Whether to test the Model.save() restoration. (default: {True})
        """
        model = instance.__class__

        self.assertEqual(
            model.objects.count(),
            expected_results['before_delete']['all']
        )
        self.assertEqual(
            model.all_objects.count(),
            expected_results['before_delete']['all_with_deleted']
        )

        if force_policy is not None:
            instance.delete(force_policy=force_policy)
        else:
            instance.delete()

        self.assertEqual(
            model.objects.count(),
            expected_results['after_delete']['all']
        )
        self.assertEqual(
            model.all_objects.count(),
            expected_results['after_delete']['all_with_deleted']
        )

        if not save:
            return

        # If there is no after_save in the expected results, then we assume
        # that Model.save will give a DoesNotExist exception because it was
        # a hard delete. So we test whether it was a hard delete.
        if 'after_save' not in expected_results:
            self.assertRaises(
                model.DoesNotExist,
                instance.refresh_from_db
            )
        else:
            instance.save()
            self.assertEqual(
                model.objects.count(),
                expected_results['after_save']['all']
            )
            self.assertEqual(
                model.all_objects.count(),
                expected_results['after_save']['all_with_deleted']
            )

    def assertSoftDelete(self, instance, force=False, **kwargs):
        """Assert whether the given model instance can be soft deleted.

        Args:
            instance: Model instance.
            force: Whether to force the soft delete policy. (default: {False})
        """
        self.assertDelete(
            instance=instance,
            expected_results={
                'before_delete': {
                    'all': 1,
                    'all_with_deleted': 1
                },
                'after_delete': {
                    'all': 0,
                    'all_with_deleted': 1
                },
                # Saving a soft deleted model should reinstate it.
                'after_save': {
                    'all': 1,
                    'all_with_deleted': 1
                },
            },
            force_policy=SOFT_DELETE if force else None,
            **kwargs
        )

    def assertHardDelete(self, instance, force=False, **kwargs):
        """Assert whether the given model instance can be hard deleted.

        Args:
            instance: Model instance.
            force: Whether to force the soft delete policy. (default: {False})
        """
        self.assertDelete(
            instance=instance,
            expected_results={
                'before_delete': {
                    'all': 1,
                    'all_with_deleted': 1
                },
                'after_delete': {
                    'all': 0,
                    'all_with_deleted': 0
                },
            },
            force_policy=HARD_DELETE if force else None,
            **kwargs
        )


class SafeDeleteForceTestCase(SafeDeleteTestCase):

    def check_skip(self):
        """Skip tests that should only run when inherited."""
        if self.__class__ == SafeDeleteForceTestCase:
            raise unittest.SkipTest(
                "Only SafeDeleteForceTestCase subclasses can have tests that use "
                "SafeDeleteForceTestCase.instance."
            )

    def test_harddelete_force(self):
        """Test whether the subclasses their instances can also be force hard deleted."""
        self.check_skip()
        self.assertHardDelete(self.instance, force=True)

    def test_softdelete_force(self):
        """Test whether the subclasses their instances can also be force soft deleted."""
        self.check_skip()
        self.assertSoftDelete(self.instance, force=True)
