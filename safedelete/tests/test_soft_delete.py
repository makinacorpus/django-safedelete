try:
    from unittest import mock
except ImportError:
    import mock

from .testcase import SafeDeleteTestCase
from ..models import SafeDeleteMixin


class SoftDeleteModel(SafeDeleteMixin):
    # SafeDeleteMixin has the soft delete policy by default
    pass


class SoftDeleteTestCase(SafeDeleteTestCase):

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
