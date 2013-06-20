
def queryset_delete(self):
    assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
    # TODO: Replace this by bulk update if we can
    for obj in self.all():
        obj.delete()
    self._result_cache = None
queryset_delete.alters_data = True

def queryset_undelete(self):
    assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
    self.all().update(deleted=False)
    self._result_cache = None
queryset_undelete.alters_data = True


def safedelete_manager_factory(superclass, allow_single_object_access):

    class SafeDeleteManager(superclass):

        # Cf. Bug XXX
        #use_for_related_fields = False
        
        def get_query_set(self):
            queryset = super(SafeDeleteManager, self).get_query_set().filter(deleted=False)
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset
            
        def all_with_deleted(self):
            queryset = super(SafeDeleteManager, self).get_query_set()
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset
        
        def only_deleted(self):
            queryset = super(SafeDeleteManager, self).get_query_set().filter(deleted=True)
            queryset.delete = queryset_delete
            queryset.undelete = queryset_undelete
            return queryset

        def filter(self, **kwargs):
            if allow_single_object_access and 'pk' in kwargs:
                return self.all_with_deleted().filter(**kwargs)
            return self.get_query_set().filter(**kwargs)

        def get(self, **kwargs):
            if allow_single_object_access:
                return self.all_with_deleted().get(**kwargs)
            return self.get_query_set().get(**kwargs)

    return SafeDeleteManager

