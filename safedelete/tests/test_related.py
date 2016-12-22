from django.db import models

from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class RelatedChild(models.Model):
    pass


class RelatedParent(SafeDeleteMixin):
    children = models.ManyToManyField(
        RelatedChild,
        blank=True,
        related_name='parents'
    )


class RelatedTestCase(SafeDeleteTestCase):

    def test_related_manager(self):
        """Test whether related queries still works."""
        parent1 = RelatedParent.objects.create()
        parent2 = RelatedParent.objects.create()
        child = RelatedChild.objects.create()

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
            child.parents.all_with_deleted().count(),
            2
        )
