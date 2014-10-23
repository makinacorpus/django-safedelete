from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


class SafeDeleteAdmin(admin.ModelAdmin):
    """
    An abstract ModelAdmin which will include deleted objects in its listing.

    :Example:

        >>> from safedelete import admin.SafeDeleteAdmin
        >>> class ContactAdmin(SafeDeleteAdmin):
        ...    list_display = ("first_name", "last_name", "email") + SafeDeleteAdmin.list_display
        ...    list_filter = ("last_name") + SafeDeleteAdmin.list_filter
    """
    undelete_selected_confirmation_template = "safedelete/undelete_selected_confirmation.html"

    list_display = ('deleted',)
    list_filter = ('deleted',)
    exclude = ('deleted',)
    actions = ('undelete_selected',)

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

    def log_undeletion(self, request, object, object_repr):
        """
        Log that an object will be undeleted.

        The default implementation creates an admin LogEntry object.
        """
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=CHANGE
        )

    def undelete_selected(self, request, queryset):
        """ Admin action to undelete objects in bulk with confirmation. """
        if not self.has_delete_permission(request):
            raise PermissionDenied
        assert hasattr(queryset, 'undelete')

        # Undeletion confirmed
        if request.POST.get('post'):
            n = queryset.count()
            if n:
                for obj in queryset:
                    obj_display = force_text(obj)
                    self.log_undeletion(request, obj, obj_display)
                queryset.undelete()
                self.message_user(
                    request,
                    _("Successfully undeleted %(count)d %(items)s.") % {
                        "count": n, "items": model_ngettext(self.opts, n)
                    },
                    messages.SUCCESS
                )
                # Return None to display the change list page again.
                return None

        opts = self.model._meta
        if len(queryset) == 1:
            objects_name = force_text(opts.verbose_name)
        else:
            objects_name = force_text(opts.verbose_name_plural)
        title = _("Are you sure?")

        context = {
            'title': title,
            'objects_name': objects_name,
            'queryset': queryset,
            "opts": opts,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }

        return TemplateResponse(
            request,
            self.undelete_selected_confirmation_template,
            context,
            current_app=self.admin_site.name,
        )
    undelete_selected.short_description = _("Undelete selected %(verbose_name_plural)s.")
