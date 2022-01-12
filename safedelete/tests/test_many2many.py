import unittest

from django.db import models

from ..config import DELETED_VISIBLE
from ..models import SafeDeleteModel
from ..fields import SafeDeleteManyToManyField
from .testcase import SafeDeleteTestCase


class ManyToManyChild(SafeDeleteModel):
    pass


class ManyToManyOtherChild(models.Model):
    pass


class ManyToManyOtherChildThrough(SafeDeleteModel):
    other_child = models.ForeignKey(ManyToManyOtherChild, on_delete=models.CASCADE)
    parent = models.ForeignKey('ManyToManyParent', on_delete=models.CASCADE)


class ManyToManyParent(SafeDeleteModel):
    children = SafeDeleteManyToManyField(
        ManyToManyChild,
        blank=True,
        related_name="parents",
    )
    other_children = models.ManyToManyField(
        ManyToManyOtherChild,
        blank=True,
        related_name='parents',
        through=ManyToManyOtherChildThrough,
    )


class ManyToManyTestCase(SafeDeleteTestCase):

    @unittest.expectedFailure
    def test_many_to_many_through(self):
        """ This is not supported yet! """
        parent = ManyToManyParent.objects.create()
        other_child = ManyToManyOtherChild.objects.create()
        through = ManyToManyOtherChildThrough.objects.create(other_child=other_child, parent=parent)

        self.assertEqual(parent.manytomanyotherchildthrough_set.all().count(), 1)
        self.assertEqual(parent.other_children.all().count(), 1)

        through.delete()

        self.assertEqual(parent.manytomanyotherchildthrough_set.all().count(), 0)
        self.assertEqual(parent.other_children.all().count(), 0)

    def test_many_to_many(self):
        """Test whether related queries still work."""
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

    def test_many_to_many_prefetch_related(self):
        """Test whether prefetch_related works as expected."""
        parent1 = ManyToManyParent.objects.create()
        parent2 = ManyToManyParent.objects.create()
        child = ManyToManyChild.objects.create()

        parent1.children.add(child)
        parent2.children.add(child)

        # Soft deleting one parent, should "hide" it from the related field
        parent1.delete()

        query = ManyToManyChild.objects.filter(id=child.id).prefetch_related("parents")
        self.assertEqual(
            len(query[0].parents.all()),
            1
        )
