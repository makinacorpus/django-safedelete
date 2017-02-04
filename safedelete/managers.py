import warnings

from django.db import models

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
        """Hook for setting custom ``_queryset_class``

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
        # We MUST NOT do the core_filters in get_queryset.
        # The child *RelatedManager will take care of that.
        # It will break prefetch_related if we do it here.
        queryset = self._queryset_class(self.model, using=self._db)

        if self._safedelete_visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD, DELETED_ONLY_VISIBLE):
            queryset = queryset.filter(
                deleted__isnull=self._safedelete_visibility in (
                    DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD
                )
            )
        return queryset

    def all_with_deleted(self):
        """Deprecated because all(show_deleted=True) is meant for related managers."""
        warnings.warn('deprecated', DeprecationWarning)
        return self.all(show_deleted=True)

    def deleted_only(self):
        """Deprecated because all(show_deleted=True) is meant for related managers."""
        warnings.warn('deprecated', DeprecationWarning)
        return self.all(show_deleted=True).filter(deleted__isnull=False)

    def all(self, show_deleted=False):
        """Override so related managers can also see the deleted models.

        A model's m2m field does not easily have access to `all_objects` and
        so setting `show_deleted` to True is a way of getting all of the
        models. It is not recommended to use `show_deleted` outside of related
        models because it will create a new queryset.

        Args:
            show_deleted: Show deleted models (default: {False})
        """
        # We need to filter if we are in a RelatedManager. See the `test_many_to_many`.
        if show_deleted:
            queryset = self._queryset_class(self.model, using=self._db)

            if hasattr(self, 'core_filters'):
                # In a RelatedManager, must filter and add hints
                queryset._add_hints(instance=self.instance)
                queryset = queryset.filter(**self.core_filters)

            return queryset
        return super(SafeDeleteManager, self).all()

    def filter(self, *args, **kwargs):
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD \
                and self._safedelete_visibility_field in kwargs:
            return self.all(show_deleted=True).filter(*args, **kwargs)
        return self.get_queryset().filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD \
                and self._safedelete_visibility_field in kwargs:
            return self.all(show_deleted=True).get(*args, **kwargs)
        return self.get_queryset().get(*args, **kwargs)


class SafeDeleteAllManager(SafeDeleteManager):

    _safedelete_visibility = DELETED_VISIBLE


class SafeDeleteDeletedManager(SafeDeleteManager):

    _safedelete_visibility = DELETED_ONLY_VISIBLE
