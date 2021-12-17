from django.db import transaction
from django.db.models import query
from django.db.models.signals import pre_delete, post_delete
from django.utils import timezone

from safedelete import utils
from safedelete.config import FIELD_NAME, SOFT_DELETE_CASCADE, NO_DELETE, SOFT_DELETE, HARD_DELETE, \
    HARD_DELETE_NOCASCADE
from .query import SafeDeleteQuery
from .signals import post_undelete, pre_softdelete, post_softdelete, pre_undelete
from .utils import related_objects

POST_SIGNAL_MARKER = 1
PRE_SIGNAL_MARKER = 2


def send_undelete_signals(active: bool, objs, signal_variety=POST_SIGNAL_MARKER):
    if not active:
        return

    signal = post_undelete if signal_variety == POST_SIGNAL_MARKER else pre_undelete
    for obj in objs:
        signal.send(sender=obj.__class__, instance=obj)


def send_delete_signals(active: bool, objs, soft=True, signal_variety=POST_SIGNAL_MARKER):
    if not active:
        return

    if soft:
        signal = post_softdelete if signal_variety == POST_SIGNAL_MARKER else pre_softdelete
        for obj in objs:
            signal.send(sender=obj.__class__, instance=obj)
    else:
        signal = post_delete if signal_variety == POST_SIGNAL_MARKER else pre_delete
        for obj in objs:
            signal.send(sender=obj.__class__, instance=obj)


def soft_delete_cascade_policy_action(objs, send_signals):
    for obj in objs:
        related_objs = related_objects(obj, return_as_dict=True)

        for model, id_list in related_objs.items():
            if utils.is_safedelete_cls(model) and hasattr(model, FIELD_NAME):
                model.objects.filter(id__in=id_list).delete(force_policy=SOFT_DELETE_CASCADE, send_signals=send_signals)


def soft_undelete_cascade_policy_action(objs, send_signals):
    for obj in objs:
        related_objs = related_objects(obj, return_as_dict=True)

        for model, id_list in related_objs.items():
            if utils.is_safedelete_cls(model) and hasattr(model, FIELD_NAME):
                model.deleted_objects.filter(id__in=id_list).exclude(
                    **{f"{FIELD_NAME}__lt": getattr(obj, FIELD_NAME)}).undelete(SOFT_DELETE_CASCADE,
                                                                                send_signals=send_signals)


class SafeDeleteQueryset(query.QuerySet):
    """Default queryset for the SafeDeleteManager.

    Takes care of "lazily evaluating" safedelete QuerySets. QuerySets passed
    within the ``SafeDeleteQueryset`` will have all of the models available.
    The deleted policy is evaluated at the very end of the chain when the
    QuerySet itself is evaluated.
    """

    def __init__(self, model=None, query=None, using=None, hints=None):
        super(SafeDeleteQueryset, self).__init__(model=model, query=query, using=using, hints=hints)
        self.query = query or SafeDeleteQuery(self.model)

    def delete(self, force_policy=None, send_signals=False):
        """Overrides bulk delete behaviour.

        .. note::
            The current implementation loses performance on bulk deletes in order
            to safely delete objects according to the deletion policies set.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.delete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."

        all_objs = self.all()
        all_objs_id_list = list(all_objs.values_list('id', flat=True))
        current_policy = force_policy or all_objs.model._safedelete_policy

        # special case when policy==HARD_DELETE_NOCASCADE
        # check if has related obj -> just mark as deleted, but not delete from DB
        if current_policy == HARD_DELETE_NOCASCADE:
            if not all(map(utils.can_hard_delete, self.model.objects.filter(id__in=all_objs_id_list))):
                current_policy = SOFT_DELETE
            else:
                current_policy = HARD_DELETE

        with transaction.atomic():
            if current_policy == NO_DELETE:
                pass

            elif current_policy == SOFT_DELETE and utils.is_safedelete_cls(self.model):
                send_delete_signals(active=send_signals, objs=all_objs, soft=True, signal_variety=PRE_SIGNAL_MARKER)
                all_objs.update(**{FIELD_NAME: timezone.now()})
                send_delete_signals(active=send_signals, objs=all_objs, soft=True, signal_variety=POST_SIGNAL_MARKER)

            elif current_policy == HARD_DELETE:
                send_delete_signals(active=send_signals, objs=all_objs, soft=False, signal_variety=PRE_SIGNAL_MARKER)
                all_objs.delete()
                send_delete_signals(active=send_signals, objs=self.model.deleted_objects.filter(id__in=all), soft=False,
                                    signal_variety=POST_SIGNAL_MARKER)

            elif current_policy == SOFT_DELETE_CASCADE:
                soft_delete_cascade_policy_action(all_objs, send_signals)

            self._result_cache = None

    delete.alters_data = True

    def undelete(self, force_policy=None, send_signals=False):
        """Undelete all soft deleted models.

        .. note::
            The current implementation loses performance on bulk undeletes in
            order to call the pre/post-save signals.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.undelete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."

        all_objs = self.all()
        all_objs_id_list = list(all_objs.values_list('id', flat=True))
        current_policy = force_policy or all_objs.model._safedelete_policy

        with transaction.atomic():
            if utils.is_safedelete_cls(all_objs.model):
                if current_policy == SOFT_DELETE_CASCADE:
                    soft_undelete_cascade_policy_action(all_objs, send_signals)

                # TODO: WTF is going on? if do not print(all_objs.query), the test_undelete_queryset() will fail.
                #   couldn't fix by myself, waiting for an answer with big the exciting
                print(all_objs.query)
                send_undelete_signals(active=send_signals, objs=all_objs, signal_variety=PRE_SIGNAL_MARKER)
                all_objs.update(**{FIELD_NAME: None})
                send_undelete_signals(active=send_signals,
                                      objs=self.model.objects.filter(id__in=all_objs_id_list),
                                      signal_variety=POST_SIGNAL_MARKER)

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
            self.query._safedelete_force_visibility = force_visibility
        return super(SafeDeleteQueryset, self).all()

    def filter(self, *args, **kwargs):
        # Return a copy, see #131
        queryset = self._clone()
        queryset.query.check_field_filter(**kwargs)
        return super(SafeDeleteQueryset, queryset).filter(*args, **kwargs)
