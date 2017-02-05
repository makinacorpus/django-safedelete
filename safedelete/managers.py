from django.db import models
from django.db.models.query_utils import Q

from .config import (DELETED_INVISIBLE, DELETED_ONLY_VISIBLE, DELETED_VISIBLE,
                     DELETED_VISIBLE_BY_FIELD)


class SafeDeleteQueryset(models.query.QuerySet):

    def delete(self):
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
        # TODO: Replace this by bulk update if we can
        for obj in self.all():
            obj.delete()
        self._result_cache = None
    delete.alters_data = True

    def undelete(self):
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
        # TODO: Replace this by bulk update if we can (need to call pre/post-save signal)
        for obj in self.all():
            obj.undelete()
        self._result_cache = None
    undelete.alters_data = True

    def all(self, force_visibility=None):
        """Override so related managers can also see the deleted models.

        A model's m2m field does not easily have access to `all_objects` and
        so setting `force_visibility` to True is a way of getting all of the
        models. It is not recommended to use `force_visibility` outside of related
        models because it will create a new queryset.

        Args:
            force_visibility: Show deleted models (default: {False})
        """
        if force_visibility is not None:
            self._safedelete_force_visibility = force_visibility
        return super(SafeDeleteQueryset, self).all()

    def _check_field_filter(self, **kwargs):
        """Check if the visibility for DELETED_VISIBLE_BY_FIELD needs t be put into effect.

        DELETED_VISIBLE_BY_FIELD is a temporary visibility flag that changes
        to DELETED_VISIBLE once asked for the named parameter defined in
        `_safedelete_force_visibility`. When evaluating the queryset, it will
        then filter on all models.
        """
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD \
                and self._safedelete_visibility_field in kwargs:
            self._safedelete_force_visibility = DELETED_VISIBLE

    def filter(self, *args, **kwargs):
        self._check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, self).filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, self).get(*args, **kwargs)

    def _filter_visibility(self):
        """Add deleted filters to the current QuerySet.

        Unlike QuerySet.filter, this does not return a clone.
        This is because QuerySet._fetch_all cannot work with a clone.
        """
        force_visibility = getattr(self, '_safedelete_force_visibility', None)
        visibility = force_visibility \
            if force_visibility is not None \
            else self._safedelete_visibility
        if visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD, DELETED_ONLY_VISIBLE):
            assert self.query.can_filter(), \
                "Cannot filter a query once a slice has been taken."

            # Add a query manually, QuerySet.filter returns a clone.
            # QuerySet._fetch_all cannot work with clones.
            self.query.add_q(
                Q(
                    deleted__isnull=visibility in (
                        DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD
                    )
                )
            )

    def __getattribute__(self, name):
        """Methods that do not return a QuerySet should call ``_filter_visibility`` first."""
        attr = object.__getattribute__(self, name)
        # These methods evaluate the queryset and therefore need to filter the
        # visiblity set.
        evaluation_methods = (
            '_fetch_all', 'count', 'exists', 'aggregate', 'update', '_update',
            'delete', 'undelete',
        )
        if hasattr(attr, '__call__') and name in evaluation_methods:
            def decorator(*args, **kwargs):
                self._filter_visibility()
                return attr(*args, **kwargs)
            return decorator
        return attr

    def _clone(self, **kwargs):
        """Called by django when cloning a QuerySet."""
        clone = super(SafeDeleteQueryset, self)._clone(**kwargs)
        clone._safedelete_visibility = self._safedelete_visibility
        clone._safedelete_visibility_field = self._safedelete_visibility_field
        if hasattr(self, '_safedelete_force_visibility'):
            clone._safedelete_force_visibility = self._safedelete_force_visibility
        return clone


class SafeDeleteManager(models.Manager):
    """
    A manager for the SafeDeleteModel.
    If _safedelete_visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.

    :attribute _safedelete_visibility: define what happens when you query masked objects.
        It can be one of ``DELETED_INVISIBLE`` and ``DELETED_VISIBLE_BY_PK``.
        Defaults to ``SOFT_DELETE``.

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
        Custom queryset classes should be inherited from ``SafeDeleteQueryset``
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
        """Pass kwargs to SafeDeleteQuerySet.all().

        Args:
            show_deleted: Show deleted models. (default: {False})

        .. note::
            The ``show_deleted`` argument is meant for related managers when no
            other managers like ``all_objects`` or ``deleted_objects`` are available.
        """
        # get_queryset().all(**kwargs) is used instead of a get_queryset(**kwargs)
        # implementation because get_queryset() is different for related managers.
        return self.get_queryset().all(**kwargs)


class SafeDeleteAllManager(SafeDeleteManager):
    """SafeDeleteManager with ``_safedelete_visibility`` set to ``DELETED_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedelete.models.SafeDeleteModel.all_objects`
    """

    _safedelete_visibility = DELETED_VISIBLE


class SafeDeleteDeletedManager(SafeDeleteManager):
    """SafeDeleteManager with ``_safedelete_visibility`` set to ``DELETED_ONLY_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedelete.models.SafeDeleteModel.deleted_objects`
    """

    _safedelete_visibility = DELETED_ONLY_VISIBLE
