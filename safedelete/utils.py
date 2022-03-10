import itertools
import warnings
from collections import defaultdict

from django.contrib.admin.utils import NestedObjects
from django.db import router
from django.db.models.query import QuerySet


def related_objects(obj, return_as_dict=False):
    """ Return a generator to the objects that would be deleted if we delete "obj" (excluding obj) """

    collector = NestedObjects(using=router.db_for_write(obj))
    collector.collect([obj])

    if return_as_dict:
        def to_dict(elem, result_dict):
            if isinstance(elem, list) or isinstance(elem, QuerySet):
                return list(map(lambda elem: to_dict(elem, result_dict), elem))
            elif obj != elem:
                result_dict[elem._meta.model].append(elem.id)

        result_dict = defaultdict(list)
        to_dict(collector.nested(), result_dict)

        return result_dict

    def flatten(elem):
        if isinstance(elem, list) or isinstance(elem, QuerySet):
            return itertools.chain.from_iterable(map(flatten, elem))
        elif obj != elem:
            return (elem,)
        return ()

    return flatten(collector.nested())


def can_hard_delete(obj):
    return not bool(list(related_objects(obj)))


def is_safedelete_cls(cls):
    for base in cls.__bases__:
        # This used to check if it startswith 'safedelete', but that masks
        # the issue inside of a test. Other clients create models that are
        # outside of the safedelete package.
        if base.__module__.startswith('safedelete.models'):
            return True
        if is_safedelete_cls(base):
            return True
    return False


def is_safedelete(related):
    warnings.warn(
        'is_safedelete is deprecated in favor of is_safedelete_cls',
        DeprecationWarning)
    return is_safedelete_cls(related.__class__)
