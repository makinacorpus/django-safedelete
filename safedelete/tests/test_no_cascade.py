from django.db import models
from django.db.models.deletion import ProtectedError

from . import SafeDeleteTestCase
from ..config import HARD_DELETE_NOCASCADE
from ..models import SafeDeleteMixin


class NoCascadeModel(SafeDeleteMixin):
    _safedelete_policy = HARD_DELETE_NOCASCADE


class CascadeChild(models.Model):
    parent = models.ForeignKey(
        NoCascadeModel,
        on_delete=models.CASCADE
    )


class ProtectedChild(SafeDeleteMixin):
    parent = models.ForeignKey(
        NoCascadeModel,
        on_delete=models.PROTECT
    )


class NullChild(SafeDeleteMixin):
    parent = models.ForeignKey(
        NoCascadeModel,
        on_delete=models.SET_NULL,
        null=True
    )


class DefaultChild(SafeDeleteMixin):
    parent = models.ForeignKey(
        NoCascadeModel,
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None
    )


def get_default():
    return None


class SetChild(SafeDeleteMixin):
    parent = models.ForeignKey(
        NoCascadeModel,
        on_delete=models.SET(get_default),
        null=True,
        default=None
    )


class NoCascadeTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.instance = NoCascadeModel.objects.create()

    def test_cascade(self):
        cascade_child = CascadeChild.objects.create(
            parent=self.instance
        )
        self.assertSoftDelete(self.instance)
        cascade_child.delete()
        self.assertHardDelete(self.instance)

    def test_protected(self):
        ProtectedChild.objects.create(
            parent=self.instance
        )
        self.assertRaises(
            ProtectedError,
            self.instance.delete
        )

    def test_null(self):
        NullChild.objects.create(
            parent=self.instance
        )
        self.assertHardDelete(self.instance)

    def test_default(self):
        DefaultChild.objects.create(
            parent=self.instance
        )
        self.assertHardDelete(self.instance)

    def test_set(self):
        SetChild.objects.create(
            parent=self.instance
        )
        self.assertHardDelete(self.instance)

    def test_harddelete_force(self):
        self.assertHardDelete(self.instance, force=True)

    def test_softdelete_force(self):
        self.assertSoftDelete(self.instance, force=True)
