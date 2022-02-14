from django.test import TestCase

from ..config import (
    HARD_DELETE,
    HARD_DELETE_NOCASCADE,
    NO_DELETE,
    SOFT_DELETE,
    SOFT_DELETE_CASCADE,
)
from ..models import SafeDeleteModel


class TestDeleteModel(SafeDeleteModel):
    def __init__(self, *args, **kwargs):
        # Initialize a counter to count the number of times delete method is called.
        self.delete_call_counter = 0
        super().__init__(*args, **kwargs)

    def delete(self, force_policy=None, **kwargs):
        super().delete(force_policy, **kwargs)
        # Add counter on every delete method call
        self.delete_call_counter += 1


class TestSingleDeleteCallOnInheritance(TestCase):
    '''Call delete for every policy and test if `delete_call_counter == 1`'''

    def test_single_delete_call_for_no_delete(self):
        instance = TestDeleteModel.objects.create()
        instance.delete(force_policy=NO_DELETE)
        # test NO_DELETE
        self.assertEqual(instance.delete_call_counter, 1)

    def test_single_delete_call_for_soft_delete(self):
        instance = TestDeleteModel.objects.create()
        instance.delete(force_policy=SOFT_DELETE)
        # test SOFT_DELETE
        self.assertEqual(instance.delete_call_counter, 1)

    def test_single_delete_call_for_soft_delete_cascade(self):
        instance = TestDeleteModel.objects.create()
        instance.delete(force_policy=SOFT_DELETE_CASCADE)
        # test SOFT_DELETE_CASCADE
        self.assertEqual(instance.delete_call_counter, 1)

    def test_single_delete_call_for_hard_delete(self):
        instance = TestDeleteModel.objects.create()
        instance.delete(force_policy=HARD_DELETE)
        # test HARD_DELETE
        self.assertEqual(instance.delete_call_counter, 1)
        with self.assertRaises(TestDeleteModel.DoesNotExist):
            TestDeleteModel.objects.get(pk=instance.pk)

    def test_single_delete_call_for_hard_delete_nocascade(self):
        instance = TestDeleteModel.objects.create()
        instance.delete(force_policy=HARD_DELETE_NOCASCADE)
        # test HARD_DELETE_NOCASCADE
        self.assertEqual(instance.delete_call_counter, 1)
