from django.db import models

from ..config import DELETED_VISIBLE
from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class ManyToManyChild(models.Model):
    pass


class ManyToManyParent(SafeDeleteModel):
    children = models.ManyToManyField(
        ManyToManyChild,
        blank=True,
        related_name='parents'
    )


class ManyToManyTestCase(SafeDeleteTestCase):

    def test_many_to_many(self):
        """Test whether related queries still works."""
        parent1 = ManyToManyParent.objects.create()
        parent2 = ManyToManyParent.objects.create()
        child = ManyToManyChild.objects.create()

        parent1.children.add(child)
        parent2.children.add(child)

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
