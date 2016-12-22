import mock
from django.test import TestCase

from ..models import SafeDeleteMixin


class SoftDeleteModel(SafeDeleteMixin):
    # SafeDeleteMixin has the soft delete policy by default
    pass


class SoftDeleteTestCase(TestCase):

    def setUp(self):
        self.instance = SoftDeleteModel.objects.create()

    def test_softdelete(self):
        self.assertEqual(
            SoftDeleteModel.objects.count(),
            1
        )
        self.assertEqual(
            SoftDeleteModel.objects.all_with_deleted().count(),
            1
        )

        self.instance.delete()
        self.assertEqual(
            SoftDeleteModel.objects.count(),
            0
        )
        self.assertEqual(
            SoftDeleteModel.objects.all_with_deleted().count(),
            1
        )

        self.instance.save()
        self.assertEqual(
            SoftDeleteModel.objects.count(),
            1
        )
        self.assertEqual(
            SoftDeleteModel.objects.all_with_deleted().count(),
            1
        )

    @mock.patch('safedelete.models.post_undelete.send')
    @mock.patch('safedelete.models.post_softdelete.send')
    def test_signals(self, mock_softdelete, mock_undelete):
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
