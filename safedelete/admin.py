import django
from distutils.version import LooseVersion
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.utils import model_ngettext
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _


def highlight_deleted(obj):
    """
        Display in red lines when object is deleted.
    """
    obj_str = conditional_escape(text_type(obj))
    if not getattr(obj, 'deleted', False):
        return obj_str
    else:
        return format_html('<span class="deleted">{0}</span>', obj_str)


highlight_deleted.short_description = _("Name")


class SafeDeleteAdmin(admin.ModelAdmin):
    """
    An abstract ModelAdmin which will include deleted objects in its listing.

    :Example:

        >>> from safedelete.admin import SafeDeleteAdmin, highlight_deleted
        >>> class ContactAdmin(SafeDeleteAdmin):
        ...    list_display = (highlight_deleted, "first_name", "last_name", "email") + SafeDeleteAdmin.list_display
        ...    list_filter = ("last_name") + SafeDeleteAdmin.list_filter
    """
    undelete_selected_confirmation_template = "safedelete/undelete_selected_confirmation.html"

    list_display = ('deleted',)
    list_filter = ('deleted',)
    exclude = ('deleted',)
    actions = ('undelete_selected',)

    class Meta:
        abstract = True

    class Media:
        css = {
            'all': ('safedelete/admin.css',),
        }

    def queryset(self, request):
        # Deprecated in latest Django versions
        return self.get_queryset(request)

    def get_queryset(self, request):
        try:
            queryset = self.model.all_objects.all()
        except:
            queryset = self.model._default_manager.all()

        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def log_undeletion(self, request, obj, object_repr):
        """
        Log that an object will be undeleted.

        The default implementation creates an admin LogEntry object.
        """
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(self.model).pk,
            object_id=obj.pk,
            object_repr=object_repr,
            action_flag=CHANGE
        )

    def undelete_selected(self, request, queryset):
        """ Admin action to undelete objects in bulk with confirmation. """
        if not self.has_delete_permission(request):
            raise PermissionDenied
        assert hasattr(queryset, 'undelete')

        # Remove not deleted item from queryset
        queryset = queryset.filter(deleted__isnull=False)
        # Undeletion confirmed
        if request.POST.get('post'):
            n = queryset.count()
            if n:
                for obj in queryset:
                    obj_display = force_text(obj)
                    self.log_undeletion(request, obj, obj_display)
                queryset.undelete()
                if django.VERSION[1] <= 4:
                    self.message_user(
                        request,
                        _("Successfully undeleted %(count)d %(items)s.") % {
                            "count": n, "items": model_ngettext(self.opts, n)
                        },
                    )
                else:
                    self.message_user(
                        request,
                        _("Successfully undeleted %(count)d %(items)s.") % {
                            "count": n, "items": model_ngettext(self.opts, n)
                        },
                        messages.SUCCESS,
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
            "app_label": opts.app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }

        if LooseVersion(django.get_version()) < LooseVersion('1.10'):
            return TemplateResponse(
                request,
                self.undelete_selected_confirmation_template,
                context,
                current_app=self.admin_site.name,
            )
        else:
            return TemplateResponse(
                request,
                self.undelete_selected_confirmation_template,
                context,
            )
    undelete_selected.short_description = _("Undelete selected %(verbose_name_plural)s.")
