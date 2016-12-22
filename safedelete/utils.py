import itertools

from django.db import router

try:
    # Django 1.7
    from django.contrib.admin.utils import NestedObjects
except ImportError:
    # Django < 1.7
    from django.contrib.admin.util import NestedObjects


def can_hard_delete(obj):
    collector = NestedObjects(using=router.db_for_write(obj))
    collector.collect([obj])

    def flatten(elem):
        if isinstance(elem, list):
            return itertools.chain.from_iterable(map(flatten, elem))
        elif obj != elem:
            return (elem,)
        return ()

    return not bool(list(flatten(collector.nested())))
