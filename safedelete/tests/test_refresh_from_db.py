from ..config import DELETED_VISIBLE_BY_FIELD
from ..managers import SafeDeleteManager
from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class FieldManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_FIELD


class RefreshModel(SafeDeleteMixin):
    objects = FieldManager()


class RefreshTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = RefreshModel.objects.create()

    def test_visible_by_field(self):
        """Refresh should work with DELETED_VISIBLE_BY_FIELD."""
        self.instance.refresh_from_db()

        self.instance.delete()
        self.instance.refresh_from_db()
