from django.db import models

from ..config import DELETED_VISIBLE, SOFT_DELETE_CASCADE
from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class Parent(models.Model):
    pass


class Child(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='children'
    )


class ForeignKeyTestCase(SafeDeleteTestCase):

    def test_one_to_many(self):
        """Test whether related queries still works."""
        parent = Parent.objects.create()
        child1 = Child.objects.create(parent=parent)
        Child.objects.create(parent=parent)

        # The parent should still have both children
        self.assertEqual(
            parent.children.all().count(),
            2
        )

        # Soft deleting one child, should "hide" it from the related field
        child1.delete()
        self.assertEqual(
            parent.children.all().count(),
            1
        )
        # But explicitly saying you want to "show" them, shouldn't hide them
        self.assertEqual(
            parent.children.all(force_visibility=DELETED_VISIBLE).count(),
            2
        )
