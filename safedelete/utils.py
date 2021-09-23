import itertools
from django.utils import timezone

from django.contrib.admin.utils import NestedObjects
from django.db import router
from .config import FIELD_NAME, BOOLEAN_FIELD_NAME, HAS_BOOLEAN_FIELD, USE_BOOLEAN_FIELD


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
    """Set safedelete fields with values that make an object be marked as deleted.
    Be aware of always setting both fields, so the values are in a consistent state.
    """
    setattr(obj, FIELD_NAME, timezone.now())
    if HAS_BOOLEAN_FIELD:
        setattr(obj, BOOLEAN_FIELD_NAME, True)


def mark_object_as_undeleted(obj):
    """Set safedelete fields with values that make an object be marked as not-deleted.
    Be aware of always setting both fields, so the values are in a consistent state.
    """
    setattr(obj, FIELD_NAME, None)
    if HAS_BOOLEAN_FIELD:
        setattr(obj, BOOLEAN_FIELD_NAME, False)


def assert_is_deleted(obj):
    """Check that an object is deleted. I.e. it has the FIELD_NAME with a datetime and BOOLEAN_FIELD_NAME = True"""
    assert getattr(obj, FIELD_NAME)
    if HAS_BOOLEAN_FIELD:
        assert getattr(obj, BOOLEAN_FIELD_NAME)


def get_deleted_or_not_deleted_filters_dictionary(get_deleted):
    """Return a dictionary that can be used as parameters of ORM operations, like filter or exclude.

    class Model():
        deleted_at = None

    :param get_deleted: True if you would like to filter/retrieve deleted elements,
                        False if you would like to filter/retrieve not-deleted elements.

    if {FIELD_NAME + '__isnull': True} --> Not deleted
    if {FIELD_NAME + '__isnull': False} --> Deleted elements

    Usage examples:

        # Filter deleted elements from a queryset
        filters = get_deleted_or_not_deleted_filtering_dictionary(deleted=True)
        deleted_elements_qset = queryset.filter(**filters)

        # Exclude not deleted elements from queryset
        filters = get_deleted_or_not_deleted_filtering_dictionary(deleted=False)
        deleted_elements_qset = queryset.exclude(**filters)
    """
    if USE_BOOLEAN_FIELD:
        return {BOOLEAN_FIELD_NAME: get_deleted}
    else:
        return {FIELD_NAME + '__isnull': not get_deleted}
