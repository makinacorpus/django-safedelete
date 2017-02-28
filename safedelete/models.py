import warnings

from django.db import models, router
from django.utils import timezone

from .config import (HARD_DELETE, HARD_DELETE_NOCASCADE, NO_DELETE,
                     SOFT_DELETE, SOFT_DELETE_CASCADE)
from .managers import (SafeDeleteAllManager, SafeDeleteDeletedManager,
                       SafeDeleteManager)
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

    :attribute _safedelete_policy: define what happens when you delete an object.
        It can be one of ``HARD_DELETE``, ``SOFT_DELETE``, ``SOFT_DELETE_CASCADE``, ``NO_DELETE`` and ``HARD_DELETE_NOCASCADE``.
        Defaults to ``SOFT_DELETE``.

        >>> class MyModel(SafeDeleteModel):
        ...     _safedelete_policy = SOFT_DELETE
        ...     my_field = models.TextField()
        ...
        >>> # Now you have your model (with its ``deleted`` field, and custom manager and delete method)

    :attribute objects:
        The :class:`safedelete.managers.SafeDeleteManager` that returns the non-deleted models.

    :attribute all_objects:
        The :class:`safedelete.managers.SafeDeleteAllManager` that returns the all models (non-deleted and soft-deleted).

    :attribute deleted_objects:
        The :class:`safedelete.managers.SafeDeleteDeletedManager` that returns the soft-deleted models.
    """

    _safedelete_policy = SOFT_DELETE

    deleted = models.DateTimeField(editable=False, null=True)

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
            if self.deleted and self.pk:
                was_undeleted = True
            self.deleted = None

        super(SafeDeleteModel, self).save(**kwargs)

        if was_undeleted:
            # send undelete signal
            using = kwargs.get('using') or router.db_for_write(self.__class__, instance=self)
            post_undelete.send(sender=self.__class__, instance=self, using=using)

    def undelete(self, **kwargs):
        """Undelete a soft-deleted model.

        Args:
            kwargs: Passed onto :func:`save`.

        .. note::
            Will raise a :class:`AssertionError` if the model was not soft-deleted.
        """
        assert self.deleted
        self.save(keep_deleted=False, **kwargs)

    def delete(self, force_policy=None, **kwargs):
        """Overrides Django's delete behaviour based on the model's delete policy.

        Args:
            force_policy: Force a specific delete policy. (default: {None})
            kwargs: Passed onto :func:`save` if soft deleted.
        """
        current_policy = self._safedelete_policy if (force_policy is None) else force_policy

        if current_policy == NO_DELETE:

            # Don't do anything.
            return

        elif current_policy == SOFT_DELETE:

            # Only soft-delete the object, marking it as deleted.
            self.deleted = timezone.now()
            using = kwargs.get('using') or router.db_for_write(self.__class__, instance=self)
            # send pre_softdelete signal
            pre_softdelete.send(sender=self.__class__, instance=self, using=using)
            super(SafeDeleteModel, self).save(**kwargs)
            # send softdelete signal
            post_softdelete.send(sender=self.__class__, instance=self, using=using)

        elif current_policy == HARD_DELETE:

            # Normally hard-delete the object.
            super(SafeDeleteModel, self).delete()

        elif current_policy == HARD_DELETE_NOCASCADE:

            # Hard-delete the object only if nothing would be deleted with it

            if not can_hard_delete(self):
                self.delete(force_policy=SOFT_DELETE, **kwargs)
            else:
                self.delete(force_policy=HARD_DELETE, **kwargs)

        elif current_policy == SOFT_DELETE_CASCADE:
            # Soft-delete on related objects before
            for related in related_objects(self):
                if is_safedelete_cls(related.__class__):
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

            qs = model_class.all_objects.filter(**lookup_kwargs)

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


class SafeDeleteMixin(SafeDeleteModel):
    """``SafeDeleteModel`` was previously named ``SafeDeleteMixin``.

    .. deprecated:: 0.4.0
        Use :class:`SafeDeleteModel` instead.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn('The SafeDeleteMixin class was renamed SafeDeleteModel',
                      DeprecationWarning)
        SafeDeleteModel.__init__(self, *args, **kwargs)
