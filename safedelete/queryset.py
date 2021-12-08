from django.db import transaction
from django.db.models import query
from django.db.models.signals import pre_delete
from django.utils import timezone

import safedelete.utils as safedelete_utils
from safedelete.config import FIELD_NAME, SOFT_DELETE_CASCADE, NO_DELETE, SOFT_DELETE, HARD_DELETE, \
    HARD_DELETE_NOCASCADE
from .query import SafeDeleteQuery
from .signals import post_undelete, pre_softdelete
from .utils import related_objects


def send_post_undelete_signal(objs):
    for obj in objs:
        post_undelete.send(sender=obj.__class__, instance=obj)


def send_pre_delete_signal(objs, soft=True):
    if soft:
        for obj in objs:
            pre_softdelete.send(sender=obj.__class__, instance=obj)
    else:
        for obj in objs:
            pre_delete.send(sender=obj.__class__, instance=obj)


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

    def delete(self, force_policy=None, is_pre_signalize=False):
        """Overrides bulk delete behaviour.

        .. note::
            The current implementation loses performance on bulk deletes in order
            to safely delete objects according to the deletion policies set.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.delete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."

        with transaction.atomic():
            all_objs = self.all()
            all_objs_id_list = list(all_objs.values_list('id', flat=True))
            current_policy = force_policy or all_objs.model._safedelete_policy

            if current_policy == HARD_DELETE_NOCASCADE:
                if not all(map(safedelete_utils.can_hard_delete, self.model.objects.filter(id__in=all_objs_id_list))):
                    current_policy = SOFT_DELETE
                else:
                    current_policy = HARD_DELETE

            if current_policy == NO_DELETE:
                pass

            elif current_policy == SOFT_DELETE and safedelete_utils.is_safedelete_cls(self.model):
                if is_pre_signalize:
                    send_pre_delete_signal(all_objs)
                all_objs.update(**{FIELD_NAME: timezone.now()})

            elif current_policy == HARD_DELETE:
                if is_pre_signalize:
                    send_pre_delete_signal(all_objs, soft=False)
                all_objs.delete()

            elif current_policy == SOFT_DELETE_CASCADE:
                for obj in all_objs:
                    related_objs = related_objects(obj, return_as_dict=True)

                    for model, id_list in related_objs.items():
                        if safedelete_utils.is_safedelete_cls(model) and hasattr(model, FIELD_NAME):
                            model.objects.filter(id__in=id_list).delete(current_policy)

            self._result_cache = None

    delete.alters_data = True

    def undelete(self, force_policy=None, is_post_signalize=False):
        """Undelete all soft deleted models.

        .. note::
            The current implementation loses performance on bulk undeletes in
            order to call the pre/post-save signals.

        .. seealso::
            :py:func:`safedelete.models.SafeDeleteModel.undelete`
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with undelete."
        with transaction.atomic():
            all_objs = self.all()
            all_objs_id_list = list(all_objs.values_list('id', flat=True))
            current_policy = force_policy or all_objs.model._safedelete_policy

            if current_policy == SOFT_DELETE_CASCADE:
                for obj in all_objs:
                    related_objs = related_objects(obj, return_as_dict=True)

                    if safedelete_utils.is_safedelete_cls(obj.__class__) and getattr(obj, FIELD_NAME):
                        for model, id_list in related_objs.items():
                            if safedelete_utils.is_safedelete_cls(model) and hasattr(model, FIELD_NAME):
                                model.deleted_objects.filter(
                                    id__in=id_list).exclude(
                                    **{f"{FIELD_NAME}__lt": getattr(obj, FIELD_NAME)}).undelete(current_policy)

            # TODO: WTF is going on? if do not print(all_objs.query), the test_undelete_queryset() will fail.
            #   couldn't fix by myself, waiting for an answer with big the exciting
            print(all_objs.query)
            all_objs.update(**{FIELD_NAME: None})

            if is_post_signalize:
                for obj in self.model.objects.filter(id__in=all_objs_id_list):
                    post_undelete.send(sender=obj.__class__, instance=obj)

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
