from django.db import models

from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class PrefetchBrother(SafeDeleteMixin):
    pass


class PrefetchSister(SafeDeleteMixin):
    sibling = models.ForeignKey(
        PrefetchBrother,
        related_name='sisters'
    )


class PrefetchTestCase(SafeDeleteTestCase):

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
