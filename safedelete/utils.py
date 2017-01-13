import itertools

from django.contrib.admin.utils import NestedObjects
from django.db import router


def related_objects(obj):
    """ Return a generator to the objects that would be deleted if we delete "obj" (excluding obj) """

    collector = NestedObjects(using=router.db_for_write(obj))
    collector.collect([obj])

    def flatten(elem):
        if isinstance(elem, list):
            return itertools.chain.from_iterable(map(flatten, elem))
        elif obj != elem:
            return (elem,)
        return ()

    return flatten(collector.nested())


def can_hard_delete(obj):
    return not bool(list(related_objects(obj)))
