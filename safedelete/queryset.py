from collections import Counter
from typing import Dict, Optional, Tuple, Type, TypeVar

from django.db import models
from django.db.models import query

from .config import HARD_DELETE, NO_DELETE
from .query import SafeDeleteQuery

_QS = TypeVar('_QS', bound='SafeDeleteQueryset')


class SafeDeleteQueryset(query.QuerySet):
    """Default queryset for the SafeDeleteManager.

    Takes care of "lazily evaluating" safedelete QuerySets. QuerySets passed
    within the ``SafeDeleteQueryset`` will have all of the models available.
    The deleted policy is evaluated at the very end of the chain when the
    QuerySet itself is evaluated.
    """

    def __init__(
            self,
            model: Optional[Type[models.Model]] = None,
            query: Optional[SafeDeleteQuery] = None,
            using: Optional[str] = None,
            hints: Optional[Dict[str, models.Model]] = None
    ):
        super(SafeDeleteQueryset, self).__init__(model=model, query=query, using=using, hints=hints)
        self.query: SafeDeleteQuery = query or SafeDeleteQuery(self.model)

    @classmethod
    def as_manager(cls):
        """Override as_manager behavior to ensure we create a SafeDeleteManager.
        """
        # Address the circular dependency between `SafeDeleteQueryset` and `SafeDeleteManager`.
        from .managers import SafeDeleteManager

        manager = SafeDeleteManager.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager
    as_manager.queryset_only = True  # type: ignore

    def delete(self, force_policy: Optional[int] = None) -> Tuple[int, Dict[str, int]]:
        """Overrides bulk delete behaviour.

        .. note::
            The current implementation loses performance on bulk deletes in order
            to safely delete objects according to the deletion policies set.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.delete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."

        if force_policy == NO_DELETE:
            return (0, {})
        elif force_policy == HARD_DELETE:
            return self.hard_delete_policy_action()
        else:
            deleted_counter: Counter = Counter()
            # TODO: Replace this by bulk update if we can
            for obj in self.all():
                _, delete_response = obj.delete(force_policy=force_policy)
                deleted_counter.update(delete_response)
            self._result_cache = None
            return sum(deleted_counter.values()), dict(deleted_counter)
    delete.alters_data = True  # type: ignore

    def hard_delete_policy_action(self) -> Tuple[int, Dict[str, int]]:
        # Normally hard-delete the objects.
        self.query._filter_visibility()
        return super().delete()

    def undelete(self, force_policy: Optional[int] = None) -> Tuple[int, Dict[str, int]]:
        """Undelete all soft deleted models.

        .. note::
            The current implementation loses performance on bulk undeletes in
            order to call the pre/post-save signals.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.undelete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
        undeleted_counter: Counter = Counter()
        # TODO: Replace this by bulk update if we can (need to call pre/post-save signal)
        for obj in self.all():
            _, undelete_response = obj.undelete(force_policy=force_policy)
            undeleted_counter.update(undelete_response)
        self._result_cache = None
        return sum(undeleted_counter.values()), dict(undeleted_counter)
    undelete.alters_data = True  # type: ignore

    def all(self: _QS, force_visibility=None) -> _QS:
        """Override so related managers can also see the deleted models.

        A model's m2m field does not easily have access to `all_objects` and
        so setting `force_visibility` to True is a way of getting all of the
        models. It is not recommended to use `force_visibility` outside of related
        models because it will create a new queryset.

        Args:
            force_visibility: Force a deletion visibility. (default: {None})
        """
        if force_visibility is not None:
            self.query._safedelete_force_visibility = force_visibility
        return super(SafeDeleteQueryset, self).all()

    def filter(self, *args, **kwargs):
        # Return a copy, see #131
        queryset = self._clone()
        queryset.query.check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, queryset).filter(*args, **kwargs)
