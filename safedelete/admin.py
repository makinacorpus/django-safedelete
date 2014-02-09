class SafeDeleteAdmin (admin.ModelAdmin):
    """
        from safedelete import admin.SafeDeleteAdmin
        class ContactAdmin(SafeDeleteAdmin):
            list_display = ("first_name", "last_name", "email") + SafeDeleteAdmin.list_display
            list_filter = ("last_name") + SafeDeleteAdmin.list_filter
    """
    list_display = ('deleted', )
    list_filter = ('deleted', )

    class Meta:
        abstract = True


    def queryset(self, request):
        try:
            qs = self.model._default_manager.all_with_deleted()
        except Exception as ex:
            qs = self.model._default_manager.all()

        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
