from django.contrib import admin


class SafeDeleteAdmin(admin.ModelAdmin):
    """
    An abstract ModelAdmin which will include deleted objects in its listing.

    :Example:

        >>> from safedelete import admin.SafeDeleteAdmin
        >>> class ContactAdmin(SafeDeleteAdmin):
        ...    list_display = ("first_name", "last_name", "email") \
+ SafeDeleteAdmin.list_display
        ...    list_filter = ("last_name") + SafeDeleteAdmin.list_filter
    """
    list_display = ('deleted',)
    list_filter = ('deleted',)

    class Meta:
        abstract = True

    def queryset(self, request):
        # Deprecated in latest Django versions
        return self.get_queryset(request)

    def get_queryset(self, request):
        try:
            qs = self.model._default_manager.all_with_deleted()
        except:
            qs = self.model._default_manager.all()

        if hasattr(self, 'get_ordering'):
            # Django >= 1.4
            ordering = self.get_ordering(request)
            if ordering:
                qs = qs.order_by(*ordering)
        return qs
