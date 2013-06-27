from django.db import models

from .managers import safedelete_manager_factory
from .utils import (related_objects,
                    HARD_DELETE, SOFT_DELETE, HARD_DELETE_NOCASCADE,
                    DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)


def safedelete_mixin_factory(policy,
                             visibility=DELETED_INVISIBLE,
                             manager_superclass=models.Manager,
                             queryset_superclass=models.query.QuerySet):
    """
    Returns an abstract Django model, with a ``deleted`` field.
    It will also have a custom default manager, and an overriden ``delete()`` method.

    :param policy: define what happens when you delete an object. It can be one of ``HARD_DELETE``, ``SOFT_DELETE`` and ``HARD_DELETE_NOCASCADE``.
    :param visibility: useful to define how deleted objects can be accessed. It can be ``DELETED_INVISIBLE`` (by default), or ``DELETED_VISIBLE_BY_PK``.

    :param manager_superclass: if you want, you can make your manager inherits from another class. Useful if you need to use a custom manager.
    :param queryset_superclass: the manager that will be created will return a queryset instance, which class will inherits from this class.

    :Example:

        >>> my_mixin = safedelete_mixin_factory(policy=SOFT_DELETE)
        >>> class MyModel(my_mixin):
        ...     my_field = models.TextField()
        ...
        >>> # Now you have your model (with its ``deleted`` field, and custom manager and delete method)

    """

    assert policy in (HARD_DELETE, SOFT_DELETE, HARD_DELETE_NOCASCADE)
    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    class Model(models.Model):

        deleted = models.BooleanField(default=False)

        objects = safedelete_manager_factory(manager_superclass, queryset_superclass, visibility)()

        def save(self, keep_deleted=False, **kwargs):
            """
            Save an object, un-deleting it if it was deleted.
            If you want to keep it deleted, you can set the ``keep_deleted`` argument to ``True``.
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

        class Meta:
            abstract = True

    return Model


# Often used
SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)
