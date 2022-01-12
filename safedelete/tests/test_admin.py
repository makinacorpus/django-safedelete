# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User
from django.db import models
from django.test import RequestFactory, TestCase

from ..admin import SafeDeleteAdmin, SafeDeleteAdminFilter, highlight_deleted
from ..config import FIELD_NAME
from ..models import SafeDeleteModel
from .models import Article, Author, Category


class Order(SafeDeleteModel):
    articles = models.ManyToManyField(Article)


class CategoryAdmin(SafeDeleteAdmin):
    list_display = (highlight_deleted,) + SafeDeleteAdmin.list_display


admin.site.register(Category, CategoryAdmin)


class AdminTestCase(TestCase):
    urls = 'safedelete.tests.urls'

    def setUp(self):
        self.author = Author.objects.create()

        self.categories = (
            Category.objects.create(name='é'),
            Category.objects.create(),
            Category.objects.create(),
        )

        self.articles = (
            Article(
                author=self.author
            ),
            Article(
                author=self.author,
                category=self.categories[1]
            ),
            Article(
                author=self.author,
                category=self.categories[2]
            ),
        )

        self.categories[1].delete()

        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/', {})

        self.modeladmin_default = admin.ModelAdmin(Category, AdminSite())
        self.modeladmin = CategoryAdmin(Category, AdminSite())

        user = User.objects.create_superuser('super', 'email@domain.com', 'secret')
        self.client.login(username='super', password='secret')
        self.request.user = user

    def tearDown(self):
        self.client.logout()

    def get_changelist(self, request, model, modeladmin):
        args = [
            request, model, modeladmin.list_display,
            modeladmin.list_display_links, modeladmin.list_filter,
            modeladmin.date_hierarchy, modeladmin.search_fields,
            modeladmin.list_select_related, modeladmin.list_per_page,
            modeladmin.list_max_show_all, modeladmin.list_editable,
            modeladmin
        ]
        # New parameter in Django 2.1
        if hasattr(modeladmin, 'sortable_by'):
            args.append(modeladmin.sortable_by)
        # New parameter in Django 4.0
        if hasattr(modeladmin, 'search_help_text'):
            args.append(modeladmin.search_help_text)
        return ChangeList(*args)

    def test_admin_model(self):
        changelist_default = self.get_changelist(self.request, Category, self.modeladmin_default)
        changelist = self.get_changelist(self.request, Category, self.modeladmin)
        self.assertEqual(changelist.get_filters(self.request)[0][0].title, FIELD_NAME.replace('_', ' '))
        self.assertEqual(changelist.queryset.count(), 3)
        self.assertEqual(changelist_default.queryset.count(), 2)

    def test_highlight_deleted(self):
        """Test deleted objects are in red in admin listing."""
        resp = self.client.get('/admin/safedelete/category/')
        line = '<span class="deleted">{0}</span>'.format(self.categories[1])
        self.assertContains(resp, line)

    def test_highlight_deleted_field(self):
        self.modeladmin.field_to_highlight = "name"
        self.modeladmin.list_display = ("highlight_deleted_field",)
        resp = self.client.get('/admin/safedelete/category/')
        line = '<span class="deleted">{0}</span>'.format(self.categories[1])
        self.assertContains(resp, line)

    def test_soft_delete_admin_filter(self):
        self.modeladmin.list_filter += (SafeDeleteAdminFilter,)

        with self.subTest("test_filter_unfiltered"):
            changelist = self.get_changelist(self.request, Category, self.modeladmin)
            queryset = changelist.get_queryset(self.request)
            self.assertIn(Category.all_objects.get(pk=self.categories[0].pk), queryset)
            self.assertNotIn(Category.all_objects.get(pk=self.categories[1].pk), queryset)

        with self.subTest("test_filter_equals_FIELD_NAME"):
            request = self.request_factory.get('/', {FIELD_NAME: FIELD_NAME})
            request.user = self.request.user
            changelist = self.modeladmin.get_changelist_instance(request)
            queryset = changelist.get_queryset(request)
            self.assertIn(Category.all_objects.get(pk=self.categories[0].pk), queryset)
            self.assertIn(Category.all_objects.get(pk=self.categories[1].pk), queryset)

        with self.subTest("test_filter_equals_FIELD_NAME_only"):
            request = self.request_factory.get('/', {FIELD_NAME: FIELD_NAME + '_only'})
            request.user = self.request.user
            changelist = self.modeladmin.get_changelist_instance(request)
            queryset = changelist.get_queryset(request)
            self.assertNotIn(Category.all_objects.get(pk=self.categories[0].pk), queryset)
            self.assertIn(Category.all_objects.get(pk=self.categories[1].pk), queryset)

    def test_admin_xss(self):
        """Test whether admin XSS is blocked."""
        Category.objects.create(name='<script>alert(42)</script>'),
        resp = self.client.get('/admin/safedelete/category/')
        # It should be escaped
        self.assertNotContains(resp, '<script>alert(42)</script>')

    def test_admin_undelete_action(self):
        """Test objects are undeleted and action is logged."""
        resp = self.client.post('/admin/safedelete/category/', data={
            'index': 0,
            'action': ['undelete_selected'],
            '_selected_action': [self.categories[1].pk],
        })
        self.assertTemplateUsed(resp, 'safedelete/undelete_selected_confirmation.html')
        category = Category.all_objects.get(
            pk=self.categories[1].pk
        )
        self.assertTrue(getattr(self.categories[1], FIELD_NAME))

        resp = self.client.post('/admin/safedelete/category/', data={
            'index': 0,
            'action': ['undelete_selected'],
            'post': True,
            '_selected_action': [self.categories[1].pk],
        })
        category = Category.objects.get(
            pk=self.categories[1].pk
        )
        self.assertFalse(getattr(category, FIELD_NAME))
