from django.db import models

from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class PrefetchBrother(SafeDeleteModel):
    pass


class PrefetchSister(SafeDeleteModel):
    sibling = models.ForeignKey(
        PrefetchBrother,
        related_name='sisters'
    )


class PrefetchTestCase(SafeDeleteTestCase):

    def setUp(self):
        brother1 = PrefetchBrother.objects.create()
        brother2 = PrefetchBrother.objects.create()

        PrefetchSister.objects.create(sibling=brother1)
        PrefetchSister.objects.create(sibling=brother1)
        PrefetchSister.objects.create(sibling=brother1)
        PrefetchSister.objects.create(sibling=brother1).delete()
        PrefetchSister.objects.create(sibling=brother2)
        PrefetchSister.objects.create(sibling=brother2)
        PrefetchSister.objects.create(sibling=brother2).delete()
        PrefetchSister.objects.create(sibling=brother2).delete()

    def test_prefetch_related(self):
        """prefetch_related() queryset should not be filtered by core_filter."""
        brothers = PrefetchBrother.objects.all().prefetch_related(
            'sisters'
        )
        for brother in brothers:
            self.assertQuerysetEqual(
                brother.sisters.all().order_by('pk'),
                [
                    repr(s) for s in PrefetchBrother.objects.get(
                        pk=brother.pk
                    ).sisters.all().order_by('pk')
                ]
            )

    def test_prefetch_related_is_evaluated_once(self):
        with self.assertNumQueries(2):
            brothers = PrefetchBrother.objects.all().prefetch_related('sisters')
            for brother in brothers:
                list(brother.sisters.all())
