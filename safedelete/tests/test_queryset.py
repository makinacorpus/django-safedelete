import random

from django.db import models

from ..config import DELETED_VISIBLE_BY_FIELD
from ..managers import SafeDeleteManager
from ..models import SafeDeleteMixin
from .testcase import SafeDeleteTestCase


class OtherModel(models.Model):
    pass


class FieldManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_FIELD


class QuerySetModel(SafeDeleteMixin):
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
