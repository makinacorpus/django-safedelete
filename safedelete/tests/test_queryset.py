import random

from django.db import models
from django.db.models.expressions import Exists, OuterRef

from ..config import DELETED_VISIBLE_BY_FIELD
from ..managers import SafeDeleteManager
from ..models import SafeDeleteModel
from .testcase import SafeDeleteTestCase


class OtherModel(models.Model):
    pass


class FieldManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_FIELD


class QuerySetModel(SafeDeleteModel):
    other = models.ForeignKey(
        OtherModel,
        on_delete=models.CASCADE
    )

    creation_date = models.DateTimeField('Created', auto_now_add=True)

    objects = FieldManager()


class QuerySetTestCase(SafeDeleteTestCase):

    def setUp(self):
        self.other = OtherModel.objects.create()
        self.instance = QuerySetModel.objects.create(
            other=self.other
        )
        self.instance.delete()

    def test_select_related(self):
        with self.assertNumQueries(1):
            model = QuerySetModel.objects.select_related(
                'other',
            ).get(
                pk=self.instance.pk
            )
            str(model.other)

    def test_filter_get(self):
        self.assertRaises(
            QuerySetModel.DoesNotExist,
            QuerySetModel.objects.filter(
                pk=self.instance.pk + 1,
            ).get,
            pk=self.instance.pk
        )

    def test_get_does_not_modify_the_queryset(self):
        instance = QuerySetModel.objects.create(
            other=self.other
        )
        queryset = QuerySetModel.objects.all()
        queryset.get(pk=instance.pk)
        self.assertEqual(queryset.count(), 1)

    def test_filter_filter(self):
        self.assertEqual(
            QuerySetModel.objects.filter(
                pk=self.instance.pk + 1,
            ).filter(
                pk=self.instance.pk
            ).count(),
            0
        )

    def test_get_field(self):
        QuerySetModel.objects.get(
            pk=self.instance.pk
        )

    def test_count(self):
        self.assertEqual(
            QuerySetModel.objects.count(),
            0
        )
        self.assertEqual(
            QuerySetModel.all_objects.count(),
            1
        )

    def test_iterator(self):
        self.assertEqual(
            len(list(QuerySetModel.objects.iterator())),
            0
        )
        self.assertEqual(
            len(list(QuerySetModel.all_objects.iterator())),
            1
        )

    def test_exists(self):
        self.assertFalse(
            QuerySetModel.objects.filter(
                other_id=self.other.id
            ).exists()
        )
        self.assertTrue(
            QuerySetModel.all_objects.filter(
                other_id=self.other.id
            ).exists()
        )

    def test_aggregate(self):
        self.assertEqual(
            QuerySetModel.objects.aggregate(
                max_id=models.Max('id')
            ),
            {
                'max_id': None
            }
        )
        self.assertEqual(
            QuerySetModel.all_objects.aggregate(
                max_id=models.Max('id')
            ),
            {
                'max_id': self.instance.id
            }
        )

    def test_first(self):
        self.assertEqual(
            QuerySetModel.objects.filter(id=self.instance.pk).first(),
            None)

        self.assertEqual(
            QuerySetModel.all_objects.filter(id=self.instance.pk).first(),
            self.instance)

    def test_last(self):
        self.assertEqual(
            QuerySetModel.objects.filter(id=self.instance.pk).last(),
            None)

        self.assertEqual(
            QuerySetModel.all_objects.filter(id=self.instance.pk).last(),
            self.instance)

    def test_latest(self):
        self.assertRaises(
            QuerySetModel.DoesNotExist,
            QuerySetModel.objects.filter(id=self.instance.pk).latest,
            'creation_date')

        self.assertEqual(
            QuerySetModel.all_objects.filter(id=self.instance.pk).latest('creation_date'),
            self.instance)

    def test_earliest(self):
        self.assertRaises(
            QuerySetModel.DoesNotExist,
            QuerySetModel.objects.filter(id=self.instance.pk).earliest,
            'creation_date')

        self.assertEqual(
            QuerySetModel.all_objects.filter(id=self.instance.pk).earliest('creation_date'),
            self.instance)

    def test_all(self):
        amount = random.randint(1, 4)

        # Create an other object for more testing
        [QuerySetModel.objects.create(other=self.other).delete()
         for x in range(amount)]

        self.assertEqual(
            len(QuerySetModel.objects.all()),
            0)

        self.assertEqual(
            len(QuerySetModel.all_objects.all()),
            amount + 1)  # Count for the already created instance

    def test_all_slicing(self):
        amount = random.randint(1, 4)

        # Create an other object for more testing
        [QuerySetModel.objects.create(other=self.other).delete()
         for x in range(amount)]

        self.assertEqual(
            len(QuerySetModel.objects.all()[:amount]),
            0)

        self.assertEqual(
            len(QuerySetModel.all_objects.all()[1:amount]),
            amount - 1)

    def test_values_list(self):
        instance = QuerySetModel.objects.create(
            other=self.other
        )
        self.assertEqual(
            1,
            len(QuerySetModel.objects
                .filter(id=instance.id)
                .values_list('pk', flat=True))
        )
        self.assertEqual(
            instance.id,
            QuerySetModel.objects.filter(id=instance.id).values_list('pk', flat=True)[0]
        )

    def test_union_with_different_models(self):
        """Test the safe deleted model can union with other models."""
        queryset = QuerySetModel.objects.values_list("pk")
        other_queryset = OtherModel.objects.values_list("pk")
        self.assertEqual(
            queryset.union(other_queryset).count(),
            1
        )
        self.assertEqual(
            other_queryset.union(queryset).count(),
            1
        )
        queryset = QuerySetModel.all_objects.values_list("pk")
        self.assertEqual(
            queryset.union(other_queryset, all=True).count(),
            2
        )
        self.assertEqual(
            other_queryset.union(queryset, all=True).count(),
            2
        )

    def test_union(self):
        """Test whether the soft deleted model can be found by union."""
        queryset = QuerySetModel.objects.all()
        self.assertEqual(
            queryset.union(queryset).count(),
            0
        )

        queryset = QuerySetModel.all_objects.all()
        self.assertEqual(
            queryset.union(queryset, all=False).count(),
            1
        )
        self.assertEqual(
            queryset.union(queryset, all=True).count(),
            2
        )

    def test_difference(self):
        """Test whether the soft deleted model can be found by difference."""
        instance = QuerySetModel.objects.create(
            other=self.other
        )
        queryset = QuerySetModel.objects.filter(id=instance.id)
        self.assertEqual(
            queryset.difference(
                QuerySetModel.objects.all()
            ).count(),
            0
        )

        queryset = QuerySetModel.all_objects.all()
        self.assertEqual(
            queryset.difference(
                QuerySetModel.objects.all()
            ).count(),
            1
        )
        self.assertEqual(
            queryset.difference(
                QuerySetModel.all_objects.all()
            ).count(),
            0
        )

    def test_intersection(self):
        """Test whether the soft deleted model can be found by intersection."""
        instance = QuerySetModel.objects.create(
            other=self.other
        )
        queryset = QuerySetModel.objects.filter(id=instance.id)
        self.assertEqual(
            queryset.intersection(
                QuerySetModel.objects.all()
            ).count(),
            1
        )

        queryset = QuerySetModel.all_objects.all()
        self.assertEqual(
            queryset.intersection(
                QuerySetModel.objects.all()
            ).count(),
            1
        )
        self.assertEqual(
            queryset.intersection(
                QuerySetModel.all_objects.all()
            ).count(),
            2
        )

    def test_annotation(self):
        """Test whether the soft deleted model can be found in annotation subqueries."""
        queryset = OtherModel.objects.annotate(
            has_related=Exists(QuerySetModel.objects.filter(other_id=OuterRef('pk')))
        )
        self.assertEqual(queryset.count(), 1)
        self.assertFalse(queryset[0].has_related)

    def test_delete_and_undelete_all_output(self):
        amount = random.randint(1, 4)
        for _ in range(amount):
            QuerySetModel.objects.create(other=self.other)

        delete_output = QuerySetModel.objects.all().delete()
        self.assertEqual(delete_output, (amount, {QuerySetModel._meta.label: amount}))

        delete_output = QuerySetModel.objects.all().delete()
        self.assertEqual(delete_output, (0, {}))

        undelete_output = QuerySetModel.deleted_objects.all().undelete()
        # Count for the already created instance
        self.assertEqual(undelete_output, (amount + 1, {QuerySetModel._meta.label: amount + 1}))
