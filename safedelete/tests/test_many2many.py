from ..config import DELETED_VISIBLE
from ..models import SafeDeleteModel
from ..fields import SafeDeleteManyToManyField
from .testcase import SafeDeleteTestCase


class ManyToManyChild(SafeDeleteModel):
    pass


class ManyToManyParent(SafeDeleteModel):
    children = SafeDeleteManyToManyField(
        ManyToManyChild,
        blank=True,
        related_name="parents",
    )


class ManyToManyTestCase(SafeDeleteTestCase):

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
