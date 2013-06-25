from django.db import models
from django.test import TestCase

from .models import (safedelete_mixin_factory, SoftDeleteMixin,
                     HARD_DELETE, HARD_DELETE_NOCASCADE, SOFT_DELETE,
                     DELETED_VISIBLE_BY_PK)


# MODELS (FOR TESTING)


class Author(safedelete_mixin_factory(HARD_DELETE_NOCASCADE)):
    name = models.CharField(max_length=200)


class Category(safedelete_mixin_factory(SOFT_DELETE, visibility=DELETED_VISIBLE_BY_PK)):
    name = models.CharField(max_length=200)


class Article(safedelete_mixin_factory(HARD_DELETE)):
    name = models.CharField(max_length=200)
    author = models.ForeignKey(Author)
    category = models.ForeignKey(Category, null=True, default=None)


class Order(SoftDeleteMixin):
    name = models.CharField(max_length=100)
    articles = models.ManyToManyField(Article)


# TESTS


class SimpleTest(TestCase):
    def setUp(self):

        self.authors = (
            Author(name='author 0'),
            Author(name='author 1'),
            Author(name='author 2'),
        )

        self.categories = (
            Category(name='category 0'),
            Category(name='category 1'),
            Category(name='category 2'),
        )

        for i in self.authors + self.categories:
            i.save()

        self.articles = (
            Article(name='article 0', author=self.authors[1]),
            Article(name='article 1', author=self.authors[1], category=self.categories[1]),
            Article(name='article 2', author=self.authors[2], category=self.categories[2]),
        )

        for i in self.articles:
            i.save()

        self.order = Order(name='order')
        self.order.save()
        self.order.articles.add(self.articles[0], self.articles[1])

    def test_softdelete(self):
        self.assertEqual(Order.objects.count(), 1)

        self.order.delete()

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Order.objects.all_with_deleted().count(), 1)

        self.order.save()

        self.assertEqual(Order.objects.count(), 1)

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
