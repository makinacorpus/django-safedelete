from django.db import models
from .managers import safedelete_manager_factory
from .utils import count_related_objects

# TODO: Il manque la suppression soft, mais en cascade

def safedelete_mixin_factory(
            policy_soft_delete,
            policy_hard_delete,
            allow_single_object_access=False,
            manager_superclass=models.Manager
        ):

    class Model(models.Model):
        """
        This base model provides date fields and functionality to enable logical
        delete functionality in derived models.
        """
        
        deleted = models.BooleanField(default=False)
        
        objects = safedelete_manager_factory(manager_superclass, allow_single_object_access)()
        
        def save(self, keep_deleted=False, **kwargs):
            if not keep_deleted:
                self.deleted = False
            super(Model, self).save(**kwargs)

        def undelete(self):
            assert self.deleted
            self.date_removed = False
            self.save(keep_deleted=True)

        def delete(self, force_soft_delete=None, force_hard_delete=None, **kwargs):
            soft_delete = policy_soft_delete if force_soft_delete is None else force_soft_delete
            hard_delete = policy_hard_delete if force_hard_delete is None else force_hard_delete

            if soft_delete and not hard_delete:

                # Only soft-delete the object, marking it as deleted.
                self.deleted = True
                super(Model, self).save(**kwargs)

            elif hard_delete and not soft_delete:

                # Normally hard-delete the object.
                super(Model, self).delete()

            elif hard_delete and soft_delete:

                # Hard-delete the object only if nothing would be deleted with it

                if count_related_objects(self) > 0:
                    self.delete(force_soft_delete=True, force_hard_delete=False, **kwargs)
                else:
                    self.delete(force_soft_delete=False, force_hard_delete=True, **kwargs)

            else:
                raise ValueError("soft_delete = False with hard_delete = False means nothing.")

        
        class Meta:
            abstract = True

    return Model
