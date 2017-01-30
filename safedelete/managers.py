from django.db import models

from .config import DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD


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
    A manager for the SafeDeleteMixin.
    If _safedelete_visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.

    :attribute _safedelete_visibility: define what happens when you query masked objects.
        It can be one of ``DELETED_INVISIBLE`` and ``DELETED_VISIBLE_BY_PK``.
        Defaults to ``SOFT_DELETE``.

        >>> from safedelete.models import SafeDeleteMixin
        >>> from safedelete.managers import SafeDeleteManager
        >>> class MyModelManager(SafeDeleteManager):
        ...     _safedelete_visibility = DELETED_VISIBLE_BY_PK
        ...
        >>> class MyModel(SafeDeleteMixin):
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

    def get_queryset(self):
        # We MUST NOT do the core_filters in get_queryset.
        # The child *RelatedManager will take care of that.
        # It will break prefetch_related if we do it here.
        queryset = self._queryset_class(self.model, using=self._db)
        return queryset.filter(deleted__isnull=True)

    def all_with_deleted(self):
        """ Return a queryset to every objects, including deleted ones. """
        queryset = self._queryset_class(self.model, using=self._db)
        # We need to filter if we are in a RelatedManager. See the `test_related_manager`.
        if hasattr(self, 'core_filters'):
            # In a RelatedManager, must filter and add hints
            queryset._add_hints(instance=self.instance)
            queryset = queryset.filter(**self.core_filters)
        return queryset

    def deleted_only(self):
        """ Return a queryset to only deleted objects. """
        return self.all_with_deleted().filter(deleted__isnull=False)

    def filter(self, *args, **kwargs):
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD and self._safedelete_visibility_field in kwargs:
            return self.all_with_deleted().filter(*args, **kwargs)
        return self.get_queryset().filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD and self._safedelete_visibility_field in kwargs:
            return self.all_with_deleted().get(*args, **kwargs)
        return self.get_queryset().get(*args, **kwargs)

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
