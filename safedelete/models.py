import warnings

import django
from collections import Counter
from django.contrib.admin.utils import NestedObjects
from django.db import models, router
from django.db.models import UniqueConstraint
from django.utils import timezone

from .config import (
    FIELD_NAME,
    HARD_DELETE,
    HARD_DELETE_NOCASCADE,
    DELETED_BY_CASCADE_FIELD_NAME,
    NO_DELETE,
    SOFT_DELETE,
    SOFT_DELETE_CASCADE,
)
from .managers import (
    SafeDeleteAllManager,
    SafeDeleteDeletedManager,
    SafeDeleteManager,
)
from .signals import post_softdelete, post_undelete, pre_softdelete
from .utils import can_hard_delete, related_objects


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


class SafeDeleteModel(models.Model):
    """Abstract safedelete-ready model.

    .. note::
        To create your safedelete-ready models, you have to make them inherit from this model.

    :attribute deleted:
        DateTimeField set to the moment the object was deleted. Is set to
        ``None`` if the object has not been deleted.

    :attribute deleted_by_cascade:
        BooleanField set True whenever the object is deleted due cascade operation called by delete
        method of any parent Model. Default value is False. Later if its parent model calls for
        cascading undelete, it will restore only child classes that were also deleted by a cascading
        operation (deleted_by_cascade equals to True), i.e. all objects that were deleted before their
        parent deletion, should keep deleted if the same parent object is restored by undelete method.

        If this behavior isn't desired, class that inherits from SafeDeleteModel can override this
        attribute by setting it as None: overriding model class won't have its ``deleted_by_cascade``
        field and won't be restored by cascading undelete even if it was deleted by a cascade operation.

        >>> class MyModel(SafeDeleteModel):
        ...     deleted_by_cascade = None
        ...     my_field = models.TextField()

    :attribute _safedelete_policy: define what happens when you delete an object.
        It can be one of ``HARD_DELETE``, ``SOFT_DELETE``, ``SOFT_DELETE_CASCADE``, ``NO_DELETE`` and ``HARD_DELETE_NOCASCADE``.
        Defaults to ``SOFT_DELETE``.

        >>> class MyModel(SafeDeleteModel):
        ...     _safedelete_policy = SOFT_DELETE
        ...     my_field = models.TextField()
        ...
        >>> # Now you have your model (with its ``deleted`` field, and custom manager and delete method)

    :attribute objects:
        The :class:`safedelete.managers.SafeDeleteManager` returns the non-deleted models.

    :attribute all_objects:
        The :class:`safedelete.managers.SafeDeleteAllManager` returns all the models (non-deleted and soft-deleted).

    :attribute deleted_objects:
        The :class:`safedelete.managers.SafeDeleteDeletedManager` returns the soft-deleted models.
    """

    _safedelete_policy = SOFT_DELETE

    objects = SafeDeleteManager()
    all_objects = SafeDeleteAllManager()
    deleted_objects = SafeDeleteDeletedManager()

    class Meta:
        abstract = True

    def save(self, keep_deleted=False, **kwargs):
        """Save an object, un-deleting it if it was deleted.

        Args:
            keep_deleted: Do not undelete the model if soft-deleted. (default: {False})
            kwargs: Passed onto :func:`save`.

        .. note::
            Undeletes soft-deleted models by default.
        """

        # undelete signal has to happen here (and not in undelete)
        # in order to catch the case where a deleted model becomes
        # implicitly undeleted on-save.  If someone manually nulls out
        # deleted, it'll bypass this logic, which I think is fine, because
        # otherwise we'd have to shadow field changes to handle that case.

        was_undeleted = False
        if not keep_deleted:
            if getattr(self, FIELD_NAME) and self.pk:
                was_undeleted = True
            setattr(self, FIELD_NAME, None)
            setattr(self, DELETED_BY_CASCADE_FIELD_NAME, False)

        super(SafeDeleteModel, self).save(**kwargs)

        if was_undeleted:
            # send undelete signal
            using = kwargs.get('using') or router.db_for_write(self.__class__, instance=self)
            post_undelete.send(sender=self.__class__, instance=self, using=using)

    def undelete(self, force_policy=None, **kwargs):
        """Undelete a soft-deleted model.

        Args:
            force_policy: Force a specific undelete policy. (default: {None})
            kwargs: Passed onto :func:`save`.

        .. note::
            Will raise a :class:`AssertionError` if the model was not soft-deleted.
        """
        current_policy = force_policy or self._safedelete_policy

        assert getattr(self, FIELD_NAME)
        self.save(keep_deleted=False, **kwargs)
        undeleted_counter = Counter({self._meta.label: 1})

        if current_policy == SOFT_DELETE_CASCADE:
            for related in related_objects(self, only_deleted_by_cascade=True):
                if is_safedelete_cls(related.__class__) and getattr(related, FIELD_NAME):
                    _, undelete_response = related.undelete(**kwargs)
                    undeleted_counter.update(undelete_response)

        return sum(undeleted_counter.values()), dict(undeleted_counter)

    def delete(self, force_policy=None, **kwargs):
        # To know why we need to do that, see https://github.com/makinacorpus/django-safedelete/issues/117
        return self._delete(force_policy, **kwargs)

    def _delete(self, force_policy=None, **kwargs):
        """Overrides Django's delete behaviour based on the model's delete policy.

        Args:
            force_policy: Force a specific delete policy. (default: {None})
            kwargs: Passed onto :func:`save` if soft deleted.
        """
        current_policy = self._safedelete_policy if (force_policy is None) else force_policy

        if current_policy == NO_DELETE:
            return (0, {})
        elif current_policy == SOFT_DELETE:
            return self.soft_delete_policy_action(**kwargs)
        elif current_policy == HARD_DELETE:
            return self.hard_delete_policy_action(**kwargs)
        elif current_policy == HARD_DELETE_NOCASCADE:
            return self.hard_delete_cascade_policy_action(**kwargs)
        elif current_policy == SOFT_DELETE_CASCADE:
            return self.soft_delete_cascade_policy_action(**kwargs)

    def soft_delete_policy_action(self, **kwargs):
        # Only soft-delete the object, marking it as deleted.
        setattr(self, FIELD_NAME, timezone.now())

        # is_cascade shouldn't be in kwargs when calling save method.
        if kwargs.pop('is_cascade', False):
            setattr(self, DELETED_BY_CASCADE_FIELD_NAME, True)

        using = kwargs.get('using') or router.db_for_write(self.__class__, instance=self)
        # send pre_softdelete signal
        pre_softdelete.send(sender=self.__class__, instance=self, using=using)
        self.save(keep_deleted=True, **kwargs)
        # send softdelete signal
        post_softdelete.send(sender=self.__class__, instance=self, using=using)

        return (1, {self._meta.label: 1})

    def hard_delete_policy_action(self, **kwargs):
        # Normally hard-delete the object.
        return super(SafeDeleteModel, self).delete()

    def hard_delete_cascade_policy_action(self, **kwargs):
        # Hard-delete the object only if nothing would be deleted with it
        if not can_hard_delete(self):
            return self._delete(force_policy=SOFT_DELETE, **kwargs)
        else:
            return self._delete(force_policy=HARD_DELETE, **kwargs)

    def soft_delete_cascade_policy_action(self, **kwargs):
        # Soft-delete on related objects before
        deleted_counter = Counter()
        for related in related_objects(self):
            if is_safedelete_cls(related.__class__) and not getattr(related, FIELD_NAME):
                _, delete_response = related.delete(force_policy=SOFT_DELETE, is_cascade=True, **kwargs)
                deleted_counter.update(delete_response)

        # soft-delete the object
        _, delete_response = self._delete(force_policy=SOFT_DELETE, **kwargs)
        deleted_counter.update(delete_response)

        collector = NestedObjects(using=router.db_for_write(self))
        collector.collect([self])
        # update fields (SET, SET_DEFAULT or SET_NULL)
        for model, instances_for_fieldvalues in collector.field_updates.items():
            for (field, value), instances in instances_for_fieldvalues.items():
                query = models.sql.UpdateQuery(model)
                query.update_batch(
                    [obj.pk for obj in instances],
                    {field.name: value},
                    collector.using,
                )

        return sum(deleted_counter.values()), dict(deleted_counter)

    @classmethod
    def has_unique_fields(cls):
        """Checks if one of the fields of this model has a unique constraint set (unique=True).

        It also checks if the model has sets of field names that, taken together, must be unique.

        Args:
            model: Model instance to check
        """
        if cls._meta.unique_together:
            return True

        if django.VERSION[0] > 3 or (django.VERSION[0] == 3 and django.VERSION[1] >= 1):
            if cls._meta.total_unique_constraints:
                return True
        else:  # derived from total_unique_constraints in django >= 3.1
            for constraint in cls._meta.constraints:
                if isinstance(constraint, UniqueConstraint) and constraint.condition is None:
                    return True

        for field in cls._meta.fields:
            if field._unique:
                return True
        return False

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
            if hasattr(model_class, 'all_objects'):
                qs = model_class.all_objects.filter(**lookup_kwargs)
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
                errors.setdefault(key, []).append(
                    self.unique_error_message(model_class, unique_check)
                )
        return errors


SafeDeleteModel.add_to_class(FIELD_NAME, models.DateTimeField(editable=False, null=True))
SafeDeleteModel.add_to_class(DELETED_BY_CASCADE_FIELD_NAME, models.BooleanField(editable=False, default=False))


class SafeDeleteMixin(SafeDeleteModel):
    """``SafeDeleteModel`` was previously named ``SafeDeleteMixin``.

    .. deprecated:: 0.4.0
        Use :class:`SafeDeleteModel` instead.
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        warnings.warn('The SafeDeleteMixin class was renamed SafeDeleteModel',
                      DeprecationWarning)
        SafeDeleteModel.__init__(self, *args, **kwargs)
