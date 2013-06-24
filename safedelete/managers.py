from .utils import DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK

def queryset_delete(self):
    """ Delete method to be added to a queryset instance. """
    assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
    # TODO: Replace this by bulk update if we can
    for obj in self.all():
        obj.delete()
    self._result_cache = None
queryset_delete.alters_data = True

def queryset_undelete(self):
    """ Undelete method to be added to a queryset instance. """
    assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
    self.all().update(deleted=False)
    self._result_cache = None
queryset_undelete.alters_data = True


def safedelete_manager_factory(superclass, visibility=DELETED_INVISIBLE):
    """
    Return a manager, inheriting from the "superclass" class.

    If visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.
    """

    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    class SafeDeleteManager(superclass):

        # Cf. Bug XXX
        #use_for_related_fields = False
        
        def get_query_set(self):
            queryset = super(SafeDeleteManager, self).get_query_set().filter(deleted=False)
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset
            
        def all_with_deleted(self):
            """ Return a queryset to every objects, including deleted ones. """
            queryset = super(SafeDeleteManager, self).get_query_set()
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset
        
        def only_deleted(self):
            """ Return a queryset to only deleted objects. """
            queryset = super(SafeDeleteManager, self).get_query_set().filter(deleted=True)
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset

        def filter(self, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
                return self.all_with_deleted().filter(**kwargs)
            return self.get_query_set().filter(**kwargs)

        def get(self, **kwargs):
            if visibility == DELETED_VISIBLE_BY_PK:
                return self.all_with_deleted().get(**kwargs)
            return self.get_query_set().get(**kwargs)

    return SafeDeleteManager

