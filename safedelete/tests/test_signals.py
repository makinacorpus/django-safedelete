import mock
from django.test import TestCase

from ..models import SafeDeleteMixin


class SoftDeletedModel(SafeDeleteMixin):
    pass


class SignalsTestCase(TestCase):

    @mock.patch('safedelete.models.post_undelete.send')
    @mock.patch('safedelete.models.post_softdelete.send')
    def test_softdelete_signals(self, mock_softdelete, mock_undelete):
        instance = SoftDeletedModel.objects.create()

        self.assertEqual(
            SoftDeletedModel.objects.count(),
            1
        )
        instance.delete()
        self.assertEqual(
            SoftDeletedModel.objects.count(),
            0
        )
        self.assertEqual(
            SoftDeletedModel.objects.all_with_deleted().count(),
            1
        )

        # Soft deleting the model should've sent a post_softdelete signal.
        self.assertEqual(
            mock_softdelete.call_count,
            1
        )

        # Saving makes it undelete the model.
        # Undeleting a model should call the post_undelete signal.
        instance.save()
        self.assertEqual(
            mock_undelete.call_count,
            1
        )
