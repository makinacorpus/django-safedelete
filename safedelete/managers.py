from .utils import DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK


def safedelete_manager_factory(manager_superclass, queryset_superclass, visibility=DELETED_INVISIBLE):
    """
    Return a manager, inheriting from the "superclass" class.

    If visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.
    """

    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    class SafeDeleteQueryset(queryset_superclass):
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

    # Declaring the `SafeDeleteManager` as global prevents migration
    # errors (makemigrations) on Django 1.8, when for instance User model
    # is made soft-deletable.
    global SafeDeleteManager

    class SafeDeleteManager(manager_superclass):
        def get_query_set(self):
            # Deprecated in Django 1.7
            return self.get_queryset()

        def get_queryset(self):
            # We MUST NOT do the core_filters in get_queryset.
            # The child *RelatedManager will take care of that.
            # It will break prefetch_related if we do it here.
            queryset = SafeDeleteQueryset(self.model, using=self._db)
            return queryset.filter(deleted=False)

        def all_with_deleted(self):
            """ Return a queryset to every objects, including deleted ones. """
            queryset = SafeDeleteQueryset(self.model, using=self._db)
            # We need to filter if we are in a RelatedManager. See the `test_related_manager`.
            if hasattr(self, 'core_filters'):
                # In a RelatedManager, must filter and add hints
                if hasattr(queryset, '_add_hints'):
                    # Django >= 1.7
                    queryset._add_hints(instance=self.instance)
                queryset = queryset.filter(**self.core_filters)
            return queryset

        def deleted_only(self):
            """ Return a queryset to only deleted objects. """
            return self.all_with_deleted().filter(deleted=True)

        def filter(self, *args, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
                return self.all_with_deleted().filter(*args, **kwargs)
            return self.get_queryset().filter(*args, **kwargs)

        def get(self, *args, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
                return self.all_with_deleted().get(*args, **kwargs)
            return self.get_queryset().get(*args, **kwargs)

    return SafeDeleteManager
