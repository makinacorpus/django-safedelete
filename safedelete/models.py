from django.db import models
from .managers import SafeDeleteManager


def safedelete_mixin_factory(
            manager_superclass=models.Manager,
            policy_delete_soft=True,
            policy_delete_hard=True,
            policy_access_deleted=True,
        ):

    class Model(models.Model):
        """
        This base model provides date fields and functionality to enable logical
        delete functionality in derived models.
        """
        
        deleted = models.BooleanField(default=False)
        
        objects = safedelete_manager_factory(manager_superclass)()
        
        def delete(self):
            self.deleted = True
            self.save(keep_deleted=True)

        def undelete(self):
            assert self.deleted
            self.date_removed = False
            self.save(keep_deleted=True)

        def save(self, *args, **kwargs):
            if not self.keep_deleted:
                self.deleted = False
            super(Model, self).save(*args, **kwargs)
        
        class Meta:
            abstract = True

    return Model
