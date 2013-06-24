from django.db import models
from .managers import safedelete_manager_factory
from .utils import (related_objects,
                    HARD_DELETE, SOFT_DELETE, HARD_DELETE_NOCASCADE,
                    DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)


def safedelete_mixin_factory(policy,
                             visibility=DELETED_INVISIBLE,
                             manager_superclass=models.Manager):
    """
    Return an abstract Django model, with a "deleted" attribute, and a custom default manager.

    The policy attribute define what happens when you delete an object, while visibility is
    useful to define how deleted objects can be accessed.
    You can also make your manager inherits from another class (useful for GeoDjango, for instance).
    """

    assert policy in (HARD_DELETE, SOFT_DELETE, HARD_DELETE_NOCASCADE)
    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    class Model(models.Model):

        deleted = models.BooleanField(default=False)

        objects = safedelete_manager_factory(manager_superclass, visibility)()

        def save(self, keep_deleted=False, **kwargs):
            """
            Save an object, un-deleting it if it was deleted.
            If you want to keep it deleted, you can set the keep_deleted argument to True.
            """
            if not keep_deleted:
                self.deleted = False
            super(Model, self).save(**kwargs)

        def undelete(self):
            assert self.deleted
            self.save()

        def delete(self, force_policy=None, **kwargs):
            current_policy = policy if (force_policy is None) else force_policy

            if current_policy == SOFT_DELETE:

                # Only soft-delete the object, marking it as deleted.
                self.deleted = True
                super(Model, self).save(**kwargs)

            elif current_policy == HARD_DELETE:

                # Normally hard-delete the object.
                super(Model, self).delete()

            elif current_policy == HARD_DELETE_NOCASCADE:

                # Hard-delete the object only if nothing would be deleted with it

                if sum(1 for _ in related_objects(self)) > 0:
                    self.delete(force_policy=SOFT_DELETE, **kwargs)
                else:
                    self.delete(force_policy=HARD_DELETE, **kwargs)

            else:
                raise ValueError("Invalid policy for deletion.")

        class Meta:
            abstract = True

    return Model


# Often used
SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)
