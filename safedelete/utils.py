from itertools import chain

from django.contrib.admin.utils import NestedObjects
from django.db import router

from .config import DELETED_BY_CASCADE_FIELD_NAME


def related_objects(obj, only_deleted_by_cascade=False):
    """ Return a generator to the objects that would be deleted if we delete "obj" (excluding obj)

    Args:
        only_deleted_by_cascade: Include filter in flatten method to bypass elements controling undelete cascading.
    """

    collector = NestedObjects(using=router.db_for_write(obj))
    collector.collect([obj])

    def flatten(elem):
        if isinstance(elem, tuple):
            return elem
        elif obj == elem or not only_deleted_by_cascade or getattr(elem, DELETED_BY_CASCADE_FIELD_NAME, False):
            elem = [(elem,) if elem != obj else (), *collector.edges.get(elem, [])]
            return chain.from_iterable(map(flatten, elem))
        return ()

    return chain.from_iterable(map(flatten, collector.edges[None]))


def can_hard_delete(obj):
    return not bool(list(related_objects(obj)))
