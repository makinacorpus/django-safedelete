from django.db import models

from safedelete.models import SafeDeleteModel
from safedelete.tests.testcase import SafeDeleteTestCase


class Widget(models.Model):
    pass


class WidgetItem(SafeDeleteModel):
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='items',
    )


class SubQueryTestCase(SafeDeleteTestCase):

    def test_subquery_not_deleted(self):
        widget = Widget.objects.create()
        item = WidgetItem.objects.create(widget=widget)
        item_queryset = WidgetItem.objects.values_list('widget').filter(id=item.id)
        queryset = Widget.objects.filter(id__in=item_queryset)
        self.assertEqual(len(list(queryset)), 1)

    def test_subquery_deleted(self):
        widget = Widget.objects.create()
        item = WidgetItem.objects.create(widget=widget)
        item.delete()
        item_queryset = WidgetItem.objects.values_list('widget').filter(id=item.id)
        queryset = Widget.objects.filter(id__in=item_queryset)
        self.assertEqual(len(list(queryset)), 0)

    def test_subquery_same_model(self):
        widget = Widget.objects.create()
        item = WidgetItem.objects.create(widget=widget)
        item.delete()
        queryset = WidgetItem.all_objects.filter(id__in=WidgetItem.objects.all())
        self.assertEqual(len(list(queryset)), 0)
