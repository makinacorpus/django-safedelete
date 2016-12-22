from . import SafeDeleteTestCase
from ..config import HARD_DELETE
from ..models import SafeDeleteMixin


class HardDeleteModel(SafeDeleteMixin):
    _safedelete_policy = HARD_DELETE


class SoftDeleteTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = HardDeleteModel.objects.create()

    def test_harddelete(self):
        """Deleting a model with the soft delete policy should only mask it, not delete it."""
        self.assertHardDelete(self.instance)

    def test_harddelete_force(self):
        self.assertHardDelete(self.instance, force=True)

    def test_softdelete_force(self):
        self.assertSoftDelete(self.instance, force=True)
