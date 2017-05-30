from django.db import models

from .config import DELETED_INVISIBLE, DELETED_ONLY_VISIBLE, DELETED_VISIBLE
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
        queryset._safedelete_visibility = self._safedelete_visibility
        queryset._safedelete_visibility_field = self._safedelete_visibility_field
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
            show_deleted: Show deleted models. (default: {False})

        .. note::
            The ``show_deleted`` argument is meant for related managers when no
            other managers like ``all_objects`` or ``deleted_objects`` are available.
        """
        force_visibility = kwargs.pop('force_visibility', None)

        # We don't call all() on the queryset, see https://github.com/makinacorpus/django-safedelete/issues/81
        qs = self.get_queryset()
        if force_visibility is not None:
            qs._safedelete_force_visibility = force_visibility
        return qs


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
