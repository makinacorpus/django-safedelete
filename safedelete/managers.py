from django.conf import settings
from django.db import models

from .config import (
    DELETED_INVISIBLE,
    DELETED_ONLY_VISIBLE,
    DELETED_VISIBLE,
    FIELD_NAME,
    SOFT_DELETE,
    SOFT_DELETE_CASCADE,
)
from .queryset import SafeDeleteQueryset


class SafeDeleteManager(models.Manager):
    """Default manager for the SafeDeleteModel.

    If _safedelete_visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.

    :attribute _safedelete_visibility: define what happens when you query masked objects.
        It can be one of ``DELETED_INVISIBLE`` and ``DELETED_VISIBLE_BY_PK``.
        Defaults to ``DELETED_INVISIBLE``.

        >>> from safedelete.models import SafeDeleteModel
        >>> from safedelete.managers import SafeDeleteManager
        >>> class MyModelManager(SafeDeleteManager):
        ...     _safedelete_visibility = DELETED_VISIBLE_BY_PK
        ...
        >>> class MyModel(SafeDeleteModel):
        ...     _safedelete_policy = SOFT_DELETE
        ...     my_field = models.TextField()
        ...     objects = MyModelManager()
        ...
        >>>

    :attribute _queryset_class: define which class for queryset should be used
        This attribute allows to add custom filters for both deleted and not
        deleted objects. It is ``SafeDeleteQueryset`` by default.
        Custom queryset classes should be inherited from ``SafeDeleteQueryset``.
    """

    _safedelete_visibility = DELETED_INVISIBLE
    _safedelete_visibility_field = 'pk'
    _queryset_class = SafeDeleteQueryset

    def __init__(self, queryset_class=None, *args, **kwargs):
        """Hook for setting custom ``_queryset_class``.

        Example:

            class CustomQueryset(models.QuerySet):
                pass

            class MyModel(models.Model):
                my_field = models.TextField()

                objects = SafeDeleteManager(CustomQuerySet)
        """
        super(SafeDeleteManager, self).__init__(*args, **kwargs)
        if queryset_class:
            self._queryset_class = queryset_class

    def get_queryset(self):
        # Backwards compatibility, no need to move options to QuerySet.
        queryset = self._queryset_class(self.model, using=self._db)
        queryset.query._safedelete_visibility = self._safedelete_visibility
        queryset.query._safedelete_visibility_field = self._safedelete_visibility_field
        return queryset

    def all_with_deleted(self):
        """Show all models including the soft deleted models.

        .. note::
            This is useful for related managers as those don't have access to
            ``all_objects``.
        """
        return self.all(
            force_visibility=DELETED_VISIBLE
        )

    def deleted_only(self):
        """Only show the soft deleted models.

        .. note::
            This is useful for related managers as those don't have access to
            ``deleted_objects``.
        """
        return self.all(
            force_visibility=DELETED_ONLY_VISIBLE
        )

    def all(self, **kwargs):
        """Pass kwargs to ``SafeDeleteQuerySet.all()``.

        Args:
            force_visibility: Show deleted models. (default: {None})

        .. note::
            The ``force_visibility`` argument is meant for related managers when no
            other managers like ``all_objects`` or ``deleted_objects`` are available.
        """
        force_visibility = kwargs.pop('force_visibility', None)

        # We don't call all() on the queryset, see https://github.com/makinacorpus/django-safedelete/issues/81
        qs = self.get_queryset()
        if force_visibility is not None:
            qs.query._safedelete_force_visibility = force_visibility
        return qs

    def update_or_create(self, defaults=None, **kwargs):
        """See :func:`~django.db.models.Query.update_or_create.`.

        Change to regular djangoesk function:
        Regular update_or_create() fails on soft-deleted, existing record with unique constraint on non-id field
        If object is soft-deleted we don't update-or-create it but reset the deleted field to None.
        So the object is visible again like a create in any other case.

        Attention: If the object is "revived" from a soft-deleted state the created return value will
        still be false because the object is technically not created unless you set
        SAFE_DELETE_INTERPRET_UNDELETED_OBJECTS_AS_CREATED = True in the django settings.

        Args:
            defaults: Dict with defaults to update/create model instance with
            kwargs: Attributes to lookup model instance with
        """

        # Check if one of the model fields contains a unique constraint
        revived_soft_deleted_object = False
        if self.model.has_unique_fields() or 'pk' in kwargs or self.model._meta.pk.name in kwargs:
            # Check if object is already soft-deleted
            deleted_object = self.all_with_deleted().filter(**kwargs).exclude(**{FIELD_NAME: None}).first()

            # If object is soft-deleted, reset delete-state...
            if deleted_object and deleted_object._safedelete_policy in self.get_soft_delete_policies():
                setattr(deleted_object, FIELD_NAME, None)
                deleted_object.save()
                revived_soft_deleted_object = True

        # Do the standard logic
        obj, created = super(SafeDeleteManager, self).update_or_create(defaults, **kwargs)

        # If object was soft-deleted and is "revived" and settings flag is True, show object as created
        if revived_soft_deleted_object and \
                getattr(settings, 'SAFE_DELETE_INTERPRET_UNDELETED_OBJECTS_AS_CREATED', False):
            created = True

        return obj, created

    @staticmethod
    def get_soft_delete_policies():
        """Returns all states which stand for some kind of soft-delete"""
        return [SOFT_DELETE, SOFT_DELETE_CASCADE]


class SafeDeleteAllManager(SafeDeleteManager):
    """SafeDeleteManager with ``_safedelete_visibility`` set to ``DELETED_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedelete.models.SafeDeleteModel.all_objects`.
    """

    _safedelete_visibility = DELETED_VISIBLE


class SafeDeleteDeletedManager(SafeDeleteManager):
    """SafeDeleteManager with ``_safedelete_visibility`` set to ``DELETED_ONLY_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedelete.models.SafeDeleteModel.deleted_objects`.
    """

    _safedelete_visibility = DELETED_ONLY_VISIBLE
