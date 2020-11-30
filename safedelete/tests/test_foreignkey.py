from django.db import models

from ..config import DELETED_VISIBLE, SOFT_DELETE_CASCADE
from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class Child(models.Model):
    pass


class Parent(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='parents'
    )


class ForeignKeyTestCase(SafeDeleteTestCase):

    def test_many_to_many(self):
        """Test whether related queries still works."""
        child = Child.objects.create()
        parent1 = Parent.objects.create(child=child)
        Parent.objects.create(child=child)

        # The child should still have both parents
        self.assertEqual(
            child.parents.all().count(),
            2
        )

        # Soft deleting one parent, should "hide" it from the related field
        parent1.delete()
        self.assertEqual(
            child.parents.all().count(),
            1
        )
        # But explicitly saying you want to "show" them, shouldn't hide them
        self.assertEqual(
            child.parents.all(force_visibility=DELETED_VISIBLE).count(),
            2
        )
