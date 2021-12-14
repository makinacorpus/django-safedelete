from __future__ import unicode_literals

import django
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.admin.utils import model_ngettext
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.template.response import TemplateResponse
from django.utils.encoding import force_str
from django.utils.html import conditional_escape, format_html
from django.utils.translation import gettext_lazy as _
from pkg_resources import parse_version

from .config import FIELD_NAME
from .utils import related_objects

# Django 3.0 compatibility
try:
    from django.utils.six import text_type
except ImportError:
    text_type = str


def highlight_deleted(obj):
    """
        Display in red lines when object is deleted.
    """
    obj_str = conditional_escape(text_type(obj))
    if not getattr(obj, FIELD_NAME, False):
        return obj_str
    else:
        return format_html('<span class="deleted">{0}</span>', obj_str)


highlight_deleted.short_description = _("Name")


class SafeDeleteAdminFilter(admin.SimpleListFilter):
    """
        Filters objects by whether or not they have been deleted
    """
    title = _("Deleted")
    parameter_name = FIELD_NAME

    def lookups(self, request, model_admin):
        lookups = (
            (self.parameter_name, _('All (Including Deleted)')),
            (self.parameter_name + "_only", _('Deleted Only')),
        )
        return lookups

    def queryset(self, request, queryset):
        parameter_is_null = True
        if self.value() == self.parameter_name:
            return queryset
        elif self.value() == self.parameter_name + "_only":
            parameter_is_null = False
        return queryset.filter(**{self.parameter_name + '__isnull': parameter_is_null})


class SafeDeleteAdmin(admin.ModelAdmin):
    """
    An abstract ModelAdmin which will include deleted objects in its listing.

    :Example:

        >>> from safedelete.admin import SafeDeleteAdmin, SafeDeleteAdminFilter, highlight_deleted
        >>> class ContactAdmin(SafeDeleteAdmin):
        ...    list_display = (highlight_deleted, "highlight_deleted_field", "first_name", "last_name", "email") + SafeDeleteAdmin.list_display
        ...    list_filter = ("last_name", SafeDeleteAdminFilter,) + SafeDeleteAdmin.list_filter
        ...
        ...    field_to_highlight = "id"
        ...
        ... ContactAdmin.highlight_deleted_field.short_description = ContactAdmin.field_to_highlight
    """
    undelete_selected_confirmation_template = "safedelete/undelete_selected_confirmation.html"

    list_display = (FIELD_NAME,)
    list_filter = (FIELD_NAME,)
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
        except Exception:
            queryset = self.model._default_manager.all()

        if self.field_to_highlight:
            queryset = queryset.annotate(_highlighted_field=F(self.field_to_highlight))

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
        original_queryset = queryset.all()
        if not self.has_delete_permission(request):
            raise PermissionDenied
        assert hasattr(queryset, 'undelete')

        # Remove not deleted item from queryset
        queryset = queryset.filter(**{FIELD_NAME + '__isnull': False})
        # Undeletion confirmed
        if request.POST.get('post'):
            requested = queryset.count()
            if requested:
                for obj in queryset:
                    obj_display = force_str(obj)
                    self.log_undeletion(request, obj, obj_display)
                queryset.undelete()
                changed = original_queryset.filter(**{FIELD_NAME + '__isnull': True}).count()
                if changed < requested:
                    self.message_user(
                        request,
                        _("Successfully undeleted %(count_changed)d of the "
                          "%(count_requested)d selected %(items)s.") % {
                            "count_requested": requested,
                            "count_changed": changed,
                            "items": model_ngettext(self.opts, requested)
                        },
                        messages.WARNING,
                    )
                else:
                    self.message_user(
                        request,
                        _("Successfully undeleted %(count)d %(items)s.") % {
                            "count": requested,
                            "items": model_ngettext(self.opts, requested)
                        },
                        messages.SUCCESS,
                    )
                # Return None to display the change list page again.
                return None

        opts = self.model._meta
        if len(queryset) == 1:
            objects_name = force_str(opts.verbose_name)
        else:
            objects_name = force_str(opts.verbose_name_plural)
        title = _("Are you sure?")

        related_list = [list(related_objects(obj)) for obj in queryset]

        context = {
            'title': title,
            'objects_name': objects_name,
            'queryset': queryset,
            "opts": opts,
            "app_label": opts.app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'related_list': related_list
        }

        if parse_version(django.get_version()) < parse_version('1.10'):
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

    def highlight_deleted_field(self, obj):
        try:
            field_str = getattr(obj, self.field_to_highlight)
        except TypeError:
            raise ValueError("Must set field_to_highlight to your field's name (as a string)")

        field_str = conditional_escape(text_type(field_str))
        if not getattr(obj, FIELD_NAME, False):
            return field_str
        else:
            return format_html('<span class="deleted">{0}</span>', field_str)

    field_to_highlight = None
    highlight_deleted_field.short_description = _("Override this name (see docs)")
    highlight_deleted_field.admin_order_field = "_highlighted_field"

    undelete_selected.short_description = _("Undelete selected %(verbose_name_plural)s")
