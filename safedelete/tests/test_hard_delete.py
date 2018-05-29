from .testcase import SafeDeleteForceTestCase
from ..config import HARD_DELETE
from ..models import SafeDeleteModel


class HardDeleteModel(SafeDeleteModel):
    _safedelete_policy = HARD_DELETE


class SoftDeleteTestCase(SafeDeleteForceTestCase):

    def setUp(self):
        self.instance = HardDeleteModel.objects.create()

    def test_harddelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertHardDelete(self.instance)

    def test_update_or_create_no_unique_field(self):
        HardDeleteModel.objects.update_or_create(id=1)
        obj, created = HardDeleteModel.objects.update_or_create(id=1)
        self.assertEqual(obj.id, 1)
