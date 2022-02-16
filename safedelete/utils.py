from itertools import chain, filterfalse

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

    def cascade_undelete_bypass(elem):
        """ Test if elem should be bypassed by cascade undelete """

        return elem != obj and getattr(elem, DELETED_BY_CASCADE_FIELD_NAME) is False

    def replace_if_cascade_child(elem):
        """ Wraps each item in elem with tuples including their cascading child classes """

        if collector.edges.get(elem):
            return (elem, collector.edges[elem])
        else:
            return (elem,)

    def flatten(elem):
        if isinstance(elem, list):
            if only_deleted_by_cascade:
                elem = filterfalse(cascade_undelete_bypass, elem)
            expanded_elem = chain.from_iterable(map(replace_if_cascade_child, elem))
            return chain.from_iterable(map(flatten, expanded_elem))
        elif obj != elem:
            return (elem,)
        return ()

    return flatten([obj])


def can_hard_delete(obj):
    return not bool(list(related_objects(obj)))
