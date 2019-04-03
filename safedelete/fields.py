from django.db import models
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.utils.functional import cached_property

from .utils import is_safedelete_cls
from .config import DEFAULT_DELETED

__all__ = ["SafeDeleteManyToManyField"]


class SafeDeleteManyToManyField(models.ManyToManyField):
    """ManyToMany field that should be used with softdeletable through model

    Checkout models in ``test_many2many_intermediate.py``
    (``Person``, ``Group``, ``Membership``).
    ``Membership`` model may be soft-deleted, and without using this field
    this code will work incorrect:

        group = Group.objects.create(name='Cool band')
        person = Person.objects.create(name='Great singer')
        membership = Membership.objects.create(
            person=person,
            group=group,
            invite_reason='Need a new drummer'
        )
        membership.delete()
        assert group.members.count() == 0

    By default, descriptor of M2M field return all objects of related model,
    filtered just by instance (i.e. return all ``Person`` matching ``group``).

    This field just contribute special descriptor
    ``SafeDeleteManyToManyDescriptor`` that add filtration for not-deleted
    relation
    """

    def contribute_to_class(self, cls, name, **kwargs):
        """Add custom descriptor to source model"""
        super(SafeDeleteManyToManyField, self).contribute_to_class(
            cls, name, **kwargs
        )
        setattr(
            cls,
            self.name,
            SafeDeleteManyToManyDescriptor(self.remote_field, reverse=False)
        )

    def contribute_to_related_class(self, cls, related):
        """Add custom descriptor to related model"""
        super(SafeDeleteManyToManyField, self).contribute_to_related_class(
            cls, related
        )
        # this check is copied from django sources
        if not (self.remote_field.is_hidden() and
                not related.related_model._meta.swapped):
            setattr(
                cls,
                related.get_accessor_name(),
                SafeDeleteManyToManyDescriptor(self.remote_field, reverse=True)
            )


class SafeDeleteManyToManyDescriptor(ManyToManyDescriptor):
    """Custom descriptor that just change ``related_manager_cls``.

    See docstring of ``SafeDeleteManyToManyField``
    """

    @cached_property
    def related_manager_cls(self):
        """Patch default related manager with custom filter"""
        cls = super(SafeDeleteManyToManyDescriptor, self).related_manager_cls

        class SafeDeleteRelatedManager(cls):
            """Related manager with custom filtration for soft-delete"""

            def _apply_rel_filters(self, queryset):
                """Filter queryset for not deleted instances"""
                queryset = super(SafeDeleteRelatedManager, self)._apply_rel_filters(queryset)
                return queryset.filter(**self._get_safedelete_filter())

            def _get_safedelete_filter(self):
                """Build related filter dict
                Filter by the ``deleted`` attribute when relation uses an intermediate model

                Example:
                    {'membership__deleted': datetime(1970, 1, 1)}
                """
                field_name = self.query_field_name
                if is_safedelete_cls(self.through):
                    field_name = self.target_field.related_query_name()
                    filter_key = "{}__deleted".format(field_name)
                    return {filter_key: DEFAULT_DELETED}
                else:
                    return {}

        return SafeDeleteRelatedManager
