import itertools

try:
    # Django 1.7
    from django.contrib.admin.utils import NestedObjects
except ImportError:
    # Django < 1.7
    from django.contrib.admin.util import NestedObjects
from django.db import router


HARD_DELETE = 0
SOFT_DELETE = 1
SOFT_DELETE_CASCADE = 2
HARD_DELETE_NOCASCADE = 3
NO_DELETE = 4

DELETED_INVISIBLE = 10
DELETED_VISIBLE_BY_PK = 11


# FIXME: Normally we must be able to use the django Collector, not the NestedObject
#        of the admin.
#        but the django collector returns only the objects we give it, nothing more.
#        Bug ?

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
