from distutils.version import LooseVersion
import django
from django.conf.urls import patterns, include
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase, RequestFactory

from .admin import SafeDeleteAdmin, highlight_deleted
from .models import (safedelete_mixin_factory, HARD_DELETE,
                     HARD_DELETE_NOCASCADE, SOFT_DELETE, SOFT_DELETE_CASCADE,
                     NO_DELETE, DELETED_VISIBLE_BY_PK)

if LooseVersion(django.get_version()) < LooseVersion('1.9'):
    from .models import SoftDeleteMixin
else:
    from .shortcuts import SoftDeleteMixin


# MODELS (FOR TESTING)


class Author(safedelete_mixin_factory(HARD_DELETE_NOCASCADE)):
    name = models.CharField(max_length=200)


class Category(safedelete_mixin_factory(SOFT_DELETE, visibility=DELETED_VISIBLE_BY_PK)):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Article(safedelete_mixin_factory(HARD_DELETE)):
    name = models.CharField(max_length=200)
    author = models.ForeignKey(Author)
    category = models.ForeignKey(Category, null=True, default=None)

    def __unicode__(self):
        return 'Article ({0}): {1}'.format(self.pk, self.name)


class Order(SoftDeleteMixin):
    name = models.CharField(max_length=100)
    articles = models.ManyToManyField(Article)


class Press(SoftDeleteMixin):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article)


class PressNormalModel(models.Model):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article)


class VeryImportant(safedelete_mixin_factory(NO_DELETE)):
    name = models.CharField(max_length=200)


class CustomQueryset(models.query.QuerySet):
    def best(self):
        return self.filter(color='green')


class CustomManager(models.Manager):
    def best(self):
        return self.get_queryset().best()


class HasCustomQueryset(safedelete_mixin_factory(
    policy=SOFT_DELETE, manager_superclass=CustomManager, queryset_superclass=CustomQueryset)
):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=5, choices=(('red', 'Red'), ('green', 'Green')))


# ADMINMODEL (FOR TESTING)


class CategoryAdmin(SafeDeleteAdmin):
    list_display = (highlight_deleted,) + SafeDeleteAdmin.list_display

admin.site.register(Category, CategoryAdmin)

# URLS (FOR TESTING)

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
)

# TESTS


class SimpleTest(TestCase):
    def setUp(self):

        self.authors = (
            Author.objects.create(name='author 0'),
            Author.objects.create(name='author 1'),
            Author.objects.create(name='author 2'),
        )

        self.categories = (
            Category.objects.create(name='category 0'),
            Category.objects.create(name='category 1'),
            Category.objects.create(name='category 2'),
        )

        self.articles = (
            Article.objects.create(name='article 0', author=self.authors[1]),
            Article.objects.create(name='article 1', author=self.authors[1], category=self.categories[1]),
            Article.objects.create(name='article 2', author=self.authors[2], category=self.categories[2]),
        )

        self.press = (
            Press.objects.create(name='press 0', article=self.articles[2])
        )

        self.order = Order.objects.create(name='order')
        self.order.articles.add(self.articles[0], self.articles[1])

    def test_softdelete(self):
        self.assertEqual(Order.objects.count(), 1)

        self.order.delete()

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Order.objects.all_with_deleted().count(), 1)

        self.order.save()

        self.assertEqual(Order.objects.count(), 1)

    def test_soft_delete_cascade(self):
        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)

        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.objects.all_with_deleted().count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.all_with_deleted().count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.objects.all_with_deleted().count(), 1)

    def test_soft_delete_cascade_with_normal_model(self):
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.objects.all_with_deleted().count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.all_with_deleted().count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.objects.all_with_deleted().count(), 1)
        self.assertEqual(PressNormalModel.objects.count(), 1)

    def test_hard_delete(self):
        self.assertEqual(Article.objects.count(), 3)

        self.articles[0].delete()

        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.all_with_deleted().count(), 2)

        self.articles[1].delete(force_policy=SOFT_DELETE)

        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(Article.objects.all_with_deleted().count(), 2)
        self.assertEqual(Article.objects.filter(author=self.authors[2]).count(), 1)

    def test_hard_delete_nocascade(self):
        self.assertEqual(Author.objects.count(), 3)

        self.authors[0].delete()

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.objects.all_with_deleted().count(), 2)

        self.authors[1].delete()

        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(Author.objects.all_with_deleted().count(), 2)

        self.assertEqual(Article.objects.count(), 3)

    def test_no_delete(self):
        obj = VeryImportant.objects.create(name="I don't wanna die :'(.")
        obj.delete()
        self.assertEqual(obj.deleted, False)
        obj = VeryImportant.objects.get(pk=obj.pk)
        self.assertEqual(obj.deleted, False)

    def test_no_delete_manager(self):
        obj = VeryImportant.objects.create(name="I don't wanna die :'(.")
        VeryImportant.objects.all().delete()
        obj = VeryImportant.objects.get(pk=obj.pk)
        self.assertEqual(obj.deleted, False)

    def test_save(self):
        """
        When we save an object, it will be re-inserted if it was deleted,
        the same way as save() will re-insert a deleted object.
        """

        self.assertEqual(Order.objects.count(), 1)

        self.order.delete()
        self.assertEqual(Order.objects.count(), 0)

        self.order.save()
        self.assertEqual(Order.objects.count(), 1)

    def test_undelete(self):
        self.assertEqual(Order.objects.count(), 1)

        self.order.delete()
        self.assertEqual(Order.objects.count(), 0)

        self.order.undelete()
        self.assertEqual(Order.objects.count(), 1)

    def test_access_by_pk(self):
        """
        Ensure that we can access to a deleted category when we access it by pk.
        We can do that because we have set visibility=DELETED_VISIBLE_BY_PK
        """

        pk = self.categories[1].id

        self.categories[1].delete()

        self.assertRaises(Category.DoesNotExist, Category.objects.get, name=self.categories[1].name)

        self.assertEqual(self.categories[1], Category.objects.get(pk=pk))

        cat = Category.objects.filter(pk=pk)
        self.assertEqual(len(cat), 1)
        self.assertEqual(self.categories[1], cat[0])

    def test_no_access_by_pk(self):
        """
        Ensure that if we try to access a deleted object by pk (with the default visibility),
        we can't access it.
        """

        self.order.delete()

        self.assertRaises(Order.DoesNotExist, Order.objects.get, pk=self.order.id)

    def test_queryset(self):
        self.assertEqual(Category.objects.count(), 3)

        Category.objects.all().delete()

        self.assertEqual(Category.objects.count(), 0)

        Category.objects.all().undelete()  # Nonsense

        self.assertEqual(Category.objects.count(), 0)

        Category.objects.deleted_only().undelete()

        self.assertEqual(Category.objects.count(), 3)

    def test_custom_queryset_original_behavior(self):
        HasCustomQueryset.objects.create(name='Foo', color='red')
        HasCustomQueryset.objects.create(name='Bar', color='green')

        self.assertEqual(HasCustomQueryset.objects.count(), 2)
        self.assertEqual(HasCustomQueryset.objects.best().count(), 1)

    def test_related_manager(self):
        order = Order.objects.create(name='order 2')
        Order.objects.create(name='order 3')
        order.articles.add(self.articles[0])
        self.assertEqual(self.articles[0].order_set.all().count(), 2)
        order.delete()
        self.assertEqual(self.articles[0].order_set.all().count(), 1)
        # Ensure all_with_deleted() filter correctly on the article.
        self.assertEqual(
            self.articles[0].order_set.all_with_deleted().count(), 2
        )

    def test_prefetch_related(self):
        """ prefetch_related() queryset should not be filtered by core_filter """
        authors = Author.objects.all().prefetch_related('article_set')
        for author in authors:
            self.assertQuerysetEqual(
                author.article_set.all().order_by('pk'),
                [repr(a) for a in Author.objects.get(pk=author.pk).article_set.all().order_by('pk')]
            )

    def test_validate_unique(self):
        """ Check that uniqueness is also checked against deleted objects """
        Category.objects.create(name='test').delete()
        with self.assertRaises(ValidationError):
            Category(name='test').validate_unique()


class AdminTestCase(TestCase):
    urls = 'safedelete.tests'

    def setUp(self):
        self.author = Author.objects.create(name='author 0')
        self.categories = (
            Category.objects.create(name='category 0'),
            Category.objects.create(name='category 1'),
            Category.objects.create(name='category 2'),
        )
        self.articles = (
            Article(name='article 0', author=self.author),
            Article(name='article 1', author=self.author, category=self.categories[1]),
            Article(name='article 2', author=self.author, category=self.categories[2]),
        )
        self.categories[1].delete()
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/', {})
        self.modeladmin_default = admin.ModelAdmin(Category, AdminSite())
        self.modeladmin = CategoryAdmin(Category, AdminSite())
        User.objects.create_superuser("super", "", "secret")
        self.client.login(username="super", password="secret")

    def tearDown(self):
        self.client.logout()

    def get_changelist(self, request, model, modeladmin):
        return ChangeList(
            request, model, modeladmin.list_display,
            modeladmin.list_display_links, modeladmin.list_filter,
            modeladmin.date_hierarchy, modeladmin.search_fields,
            modeladmin.list_select_related, modeladmin.list_per_page,
            modeladmin.list_max_show_all, modeladmin.list_editable,
            modeladmin
        )

    def test_admin_model(self):
        changelist_default = self.get_changelist(self.request, Category, self.modeladmin_default)
        changelist = self.get_changelist(self.request, Category, self.modeladmin)
        if django.VERSION[1] == 4 or django.VERSION[1] == 5:
            # Django == 1.4 or 1.5
            self.assertEqual(changelist.get_filters(self.request)[0][0].title, "deleted")
            self.assertEqual(changelist.get_query_set(self.request).count(), 3)
            self.assertEqual(changelist_default.get_query_set(self.request).count(), 2)
        else:
            # Django >= 1.6
            self.assertEqual(changelist.get_filters(self.request)[0][0].title, "deleted")
            self.assertEqual(changelist.queryset.count(), 3)
            self.assertEqual(changelist_default.queryset.count(), 2)

    def test_admin_listing(self):
        """ Test deleted objects are in red in admin listing. """
        resp = self.client.get('/admin/safedelete/category/')
        line = '<span class="deleted">{0}</span>'.format(self.categories[1])
        self.assertContains(resp, line)

    def test_admin_xss(self):
        Category.objects.create(name='<script>alert(42)</script>'),
        resp = self.client.get('/admin/safedelete/category/')
        # It should be escaped
        self.assertNotContains(resp, '<script>alert(42)</script>')

    def test_admin_undelete_action(self):
        """ Test objects are undeleted and action is logged. """
        resp = self.client.post('/admin/safedelete/category/', data={
            'index': 0,
            'action': ['undelete_selected'],
            '_selected_action': [self.categories[1].pk],
        })
        self.assertTemplateUsed(resp, 'safedelete/undelete_selected_confirmation.html')
        category = Category.objects.get(pk=self.categories[1].pk)
        self.assertTrue(self.categories[1].deleted)

        resp = self.client.post('/admin/safedelete/category/', data={
            'index': 0,
            'action': ['undelete_selected'],
            'post': True,
            '_selected_action': [self.categories[1].pk],
        })
        category = Category.objects.get(pk=self.categories[1].pk)
        self.assertFalse(category.deleted)
