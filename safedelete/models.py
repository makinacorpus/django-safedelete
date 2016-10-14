from distutils.version import LooseVersion
from django.db import models
import django

from .managers import safedelete_manager_factory
from .utils import (related_objects,
                    HARD_DELETE, SOFT_DELETE, SOFT_DELETE_CASCADE, HARD_DELETE_NOCASCADE,
                    NO_DELETE, DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)


def safedelete_mixin_factory(policy,
                             visibility=DELETED_INVISIBLE,
                             manager_superclass=models.Manager,
                             queryset_superclass=models.query.QuerySet):
    """
    Returns an abstract Django model, with a ``deleted`` field.
    It will also have a custom default manager, and an overriden ``delete()`` method.

    :param policy: define what happens when you delete an object. It can be one of ``HARD_DELETE``, ``SOFT_DELETE`` and ``HARD_DELETE_NOCASCADE``.
    :param visibility: useful to define how deleted objects can be accessed. It can be ``DELETED_INVISIBLE`` (by default), or ``DELETED_VISIBLE_BY_PK``.

    :param manager_superclass: if you want, you can make your manager inherits from another class. Useful if you need to use a custom manager.
    :param queryset_superclass: the manager that will be created will return a queryset instance, which class will inherits from this class.

    :Example:

        >>> my_mixin = safedelete_mixin_factory(policy=SOFT_DELETE)
        >>> class MyModel(my_mixin):
        ...     my_field = models.TextField()
        ...
        >>> # Now you have your model (with its ``deleted`` field, and custom manager and delete method)

    """

    assert policy in (HARD_DELETE, SOFT_DELETE, SOFT_DELETE_CASCADE, HARD_DELETE_NOCASCADE,
                      NO_DELETE)
    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    def is_safedelete(related):
        bases = related.__class__.__bases__
        for base in bases:
            if base.__module__.startswith('safedelete'):
                return True
        return False

    class Model(models.Model):

        deleted = models.BooleanField(default=False)

        objects = safedelete_manager_factory(manager_superclass, queryset_superclass, visibility)()

        class Meta:
            abstract = True

        def save(self, keep_deleted=False, **kwargs):
            """
            Save an object, un-deleting it if it was deleted.
            If you want to keep it deleted, you can set the ``keep_deleted`` argument to ``True``.
            """
            if not keep_deleted:
                self.deleted = False
            super(Model, self).save(**kwargs)

        def undelete(self):
            assert self.deleted
            self.save(keep_deleted=False)

        def delete(self, force_policy=None, **kwargs):
            current_policy = policy if (force_policy is None) else force_policy

            if current_policy == NO_DELETE:

                # Don't do anything.
                return

            elif current_policy == SOFT_DELETE:

                # Only soft-delete the object, marking it as deleted.
                self.deleted = True
                super(Model, self).save(**kwargs)

            elif current_policy == HARD_DELETE:

                # Normally hard-delete the object.
                super(Model, self).delete()

            elif current_policy == HARD_DELETE_NOCASCADE:

                # Hard-delete the object only if nothing would be deleted with it

                if sum(1 for _ in related_objects(self)) > 0:
                    self.delete(force_policy=SOFT_DELETE, **kwargs)
                else:
                    self.delete(force_policy=HARD_DELETE, **kwargs)

            elif current_policy == SOFT_DELETE_CASCADE:
                # Soft-delete on related objects before
                for related in related_objects(self):
                    if is_safedelete(related):
                        related.delete(force_policy=SOFT_DELETE, **kwargs)
                # soft-delete the object
                self.delete(force_policy=SOFT_DELETE, **kwargs)

        # We need to overwrite this check to ensure uniqueness is also checked
        # against "deleted" (but still in db) objects.
        # FIXME: Better/cleaner way ?
        def _perform_unique_checks(self, unique_checks):
            errors = {}

            for model_class, unique_check in unique_checks:
                lookup_kwargs = {}
                for field_name in unique_check:
                    f = self._meta.get_field(field_name)
                    lookup_value = getattr(self, f.attname)
                    if lookup_value is None:
                        continue
                    if f.primary_key and not self._state.adding:
                        continue
                    lookup_kwargs[str(field_name)] = lookup_value
                if len(unique_check) != len(lookup_kwargs):
                    continue

                # This is the changed line
                if hasattr(model_class._default_manager, 'all_with_deleted'):
                    qs = model_class._default_manager.all_with_deleted().filter(**lookup_kwargs)
                else:
                    qs = model_class._default_manager.filter(**lookup_kwargs)

                model_class_pk = self._get_pk_val(model_class._meta)
                if not self._state.adding and model_class_pk is not None:
                    qs = qs.exclude(pk=model_class_pk)
                if qs.exists():
                    if len(unique_check) == 1:
                        key = unique_check[0]
                    else:
                        key = models.base.NON_FIELD_ERRORS
                    errors.setdefault(key, []).append(self.unique_error_message(model_class, unique_check))
            return errors

    return Model

# Maintains retro-compatibility with older versions, which use Django 1.9
if LooseVersion(django.get_version()) < LooseVersion('1.9'):
    SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)
    SoftDeleteCascadeMixin = safedelete_mixin_factory(SOFT_DELETE_CASCADE)
