from .testcase import SafeDeleteForceTestCase
from ..config import HARD_DELETE
from ..models import SafeDeleteMixin


class HardDeleteModel(SafeDeleteMixin):
    _safedelete_policy = HARD_DELETE


class SoftDeleteTestCase(SafeDeleteForceTestCase):

    def setUp(self):
        self.instance = HardDeleteModel.objects.create()

    def test_harddelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertHardDelete(self.instance)
