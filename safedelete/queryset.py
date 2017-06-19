from django.db.models import query
from django.db.models.query_utils import Q

from .config import (DELETED_INVISIBLE, DELETED_ONLY_VISIBLE, DELETED_VISIBLE,
                     DELETED_VISIBLE_BY_FIELD)


class SafeDeleteQueryset(query.QuerySet):
    """Default queryset for the SafeDeleteManager.

    Takes care of "lazily evaluating" safedelete QuerySets. QuerySets passed
    within the ``SafeDeleteQueryset`` will have all of the models available.
    The deleted policy is evaluated at the very end of the chain when the
    QuerySet itself is evaluated.
    """
    _safedelete_filter_applied = False

    def delete(self, force_policy=None):
        """Overrides bulk delete behaviour.

        .. note::
            The current implementation loses performance on bulk deletes in order
            to safely delete objects according to the deletion policies set.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.delete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
        # TODO: Replace this by bulk update if we can
        for obj in self.all():
            obj.delete(force_policy=force_policy)
        self._result_cache = None
    delete.alters_data = True

    def undelete(self):
        """Undelete all soft deleted models.

        .. note::
            The current implementation loses performance on bulk undeletes in
            order to call the pre/post-save signals.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.undelete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
        # TODO: Replace this by bulk update if we can (need to call pre/post-save signal)
        for obj in self.all():
            obj.undelete()
        self._result_cache = None
    undelete.alters_data = True

    def all(self, force_visibility=None):
        """Override so related managers can also see the deleted models.

        A model's m2m field does not easily have access to `all_objects` and
        so setting `force_visibility` to True is a way of getting all of the
        models. It is not recommended to use `force_visibility` outside of related
        models because it will create a new queryset.

        Args:
            force_visibility: Force a deletion visibility. (default: {None})
        """
        if force_visibility is not None:
            self._safedelete_force_visibility = force_visibility
        return super(SafeDeleteQueryset, self).all()

    def _check_field_filter(self, **kwargs):
        """Check if the visibility for DELETED_VISIBLE_BY_FIELD needs t be put into effect.

        DELETED_VISIBLE_BY_FIELD is a temporary visibility flag that changes
        to DELETED_VISIBLE once asked for the named parameter defined in
        `_safedelete_force_visibility`. When evaluating the queryset, it will
        then filter on all models.
        """
        if self._safedelete_visibility == DELETED_VISIBLE_BY_FIELD \
                and self._safedelete_visibility_field in kwargs:
            self._safedelete_force_visibility = DELETED_VISIBLE

    def filter(self, *args, **kwargs):
        self._check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, self).filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, self).get(*args, **kwargs)

    def _filter_visibility(self):
        """Add deleted filters to the current QuerySet.

        Unlike QuerySet.filter, this does not return a clone.
        This is because QuerySet._fetch_all cannot work with a clone.
        """
        force_visibility = getattr(self, '_safedelete_force_visibility', None)
        visibility = force_visibility \
            if force_visibility is not None \
            else self._safedelete_visibility
        if not self._safedelete_filter_applied and \
           visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD, DELETED_ONLY_VISIBLE):
            assert self.query.can_filter(), \
                "Cannot filter a query once a slice has been taken."

            # Add a query manually, QuerySet.filter returns a clone.
            # QuerySet._fetch_all cannot work with clones.
            self.query.add_q(
                Q(
                    deleted__isnull=visibility in (
                        DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD
                    )
                )
            )

            self._safedelete_filter_applied = True

    def __getitem__(self, key):
        """
        Override __getitem__ just before it hits the original queryset
        to apply the filter visibility method.
        """
        self._filter_visibility()

        return super(SafeDeleteQueryset, self).__getitem__(key)

    def __getattribute__(self, name):
        """Methods that do not return a QuerySet should call ``_filter_visibility`` first."""
        attr = object.__getattribute__(self, name)
        # These methods evaluate the queryset and therefore need to filter the
        # visiblity set.
        evaluation_methods = (
            '_fetch_all', 'count', 'exists', 'aggregate', 'update', '_update',
            'delete', 'undelete', 'iterator', 'first', 'last'
        )
        if hasattr(attr, '__call__') and name in evaluation_methods:
            def decorator(*args, **kwargs):
                self._filter_visibility()
                return attr(*args, **kwargs)
            return decorator
        return attr

    def _clone(self, **kwargs):
        """Called by django when cloning a QuerySet."""
        clone = super(SafeDeleteQueryset, self)._clone(**kwargs)
        clone._safedelete_visibility = self._safedelete_visibility
        clone._safedelete_visibility_field = self._safedelete_visibility_field
        clone._safedelete_filter_applied = self._safedelete_filter_applied
        if hasattr(self, '_safedelete_force_visibility'):
            clone._safedelete_force_visibility = self._safedelete_force_visibility
        return clone
