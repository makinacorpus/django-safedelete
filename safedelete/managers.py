from .utils import DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK


class SafeDeleteQuerysetMixin(object):
    def delete(self):
        assert self.query.can_filter(), \
            "Cannot use 'limit' or 'offset' with delete."
        # TODO: Replace this by bulk update if we can
        for obj in self.all():
            obj.delete()
        self._result_cache = None
    delete.alters_data = True

    def undelete(self):
        assert self.query.can_filter(), \
            "Cannot use 'limit' or 'offset' with undelete."
        # TODO: Replace this by bulk update if we can
        # (need to call pre/post-save signal)
        for obj in self.all():
            obj.undelete()
        self._result_cache = None
    undelete.alters_data = True


class SafeDeleteManagerMixin(object):
    use_for_related_fields = True

    def get_query_set(self):
        # Deprecated in Django 1.7
        return self.get_queryset()

    def get_queryset(self):
        # We MUST NOT do the core_filters in get_queryset.
        # The child *RelatedManager will take care of that.
        # It will break prefetch_related if we do it here.
        queryset = self._get_queryset_cls()(self.model, using=self._db)
        return queryset.filter(deleted=False)

    def all_with_deleted(self):
        """ Return a queryset to every objects, including deleted ones. """
        queryset = self._get_queryset_cls()(self.model, using=self._db)
        # We need to filter if we are in a RelatedManager. See the `test_related_manager`.
        if hasattr(self, 'core_filters'):
            # In a RelatedManager, must filter and add hints
            if hasattr(queryset, '_add_hints'):
                # Django >= 1.7
                queryset._add_hints(instance=self.instance)
            queryset = queryset.filter(**self.core_filters)
        return queryset

    def deleted_only(self):
        """ Return a queryset to only deleted objects. """
        return self.all_with_deleted().filter(deleted=True)

    def filter(self, *args, **kwargs):
        if self._get_visibility() == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
            return self.all_with_deleted().filter(*args, **kwargs)
        return self.get_queryset().filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self._get_visibility() == DELETED_VISIBLE_BY_PK and 'pk' in kwargs:
            return self.all_with_deleted().get(*args, **kwargs)
        return self.get_queryset().get(*args, **kwargs)


def safedelete_manager_factory(manager_superclass, queryset_superclass, visibility=DELETED_INVISIBLE):
    """
    Return a manager, inheriting from the "superclass" class.

    If visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.
    """

    assert visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)

    # this still will fail if multiple copies of the same params are passed;
    # it's just generally a bad pattern
    sdqs_classname = '{0}SafeDeleteQueryset'.format(
        queryset_superclass.__name__)

    SafeDeleteQueryset = globals()[sdqs_classname] = type(
        sdqs_classname, (SafeDeleteQuerysetMixin, queryset_superclass), {})

    def _get_visibility(self):
        return visibility

    def _get_queryset_cls(self):
        return SafeDeleteQueryset

    sdm_classname = '{0}SafeDeleteManager'.format(
        manager_superclass.__name__)

    SafeDeleteManager = globals()[sdm_classname] = type(
        sdm_classname, (SafeDeleteManagerMixin, manager_superclass), {
            '_get_visibility': _get_visibility,
            '_get_queryset_cls': _get_queryset_cls
        })

    return SafeDeleteManager
