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
