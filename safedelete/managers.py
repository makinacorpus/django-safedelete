from django.db import models
from django.db.models.query import QuerySet


class SafeDeleteQuerySet(QuerySet):
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
    

def safedelete_manager_factory(superclass):

    class SafeDeleteManager(superclass):

        # Cf. Bug XXX
        #use_for_related_fields = False
        
        def get_queryset(self):
            return SafeDeleteQuerySet(self.model, using=self._db).filter(deleted=False)
        
        def all_with_deleted(self):
            return SafeDeleteQuerySet(self.model, using=self._db)
        
        def only_deleted(self):
            return SafeDeleteQuerySet(self.model, using=self._db).filter(deleted=True)

    return SafeDeleteManager

