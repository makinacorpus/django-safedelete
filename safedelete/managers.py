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
            self.all().update(deleted=False)
            self._result_cache = None
        undelete.alters_data = True

    class SafeDeleteManager(manager_superclass):
        def get_query_set(self):
            return self.all_with_deleted().filter(deleted=False)

        def all_with_deleted(self):
            """ Return a queryset to every objects, including deleted ones. """
            return SafeDeleteQueryset(self.model, using=self._db)

        def deleted_only(self):
            """ Return a queryset to only deleted objects. """
            return self.all_with_deleted().filter(deleted=True)

        def filter(self, *args, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
                return self.all_with_deleted().filter(*args, **kwargs)
            return self.get_query_set().filter(*args, **kwargs)

        def get(self, *args, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
                return self.all_with_deleted().get(*args, **kwargs)
            return self.get_query_set().get(*args, **kwargs)

    return SafeDeleteManager
