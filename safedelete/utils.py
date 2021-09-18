import itertools
from django.utils import timezone

from django.contrib.admin.utils import NestedObjects
from django.db import router
from .config import FIELD_NAME, BOOLEAN_FIELD_NAME, HAS_BOOLEAN_FIELD


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


def mark_object_as_deleted(obj):
    setattr(obj, FIELD_NAME, timezone.now())
    if HAS_BOOLEAN_FIELD:
        setattr(obj, BOOLEAN_FIELD_NAME, True)


def mark_object_as_undeleted(obj):
    setattr(obj, FIELD_NAME, None)
    if HAS_BOOLEAN_FIELD:
        setattr(obj, BOOLEAN_FIELD_NAME, False)
