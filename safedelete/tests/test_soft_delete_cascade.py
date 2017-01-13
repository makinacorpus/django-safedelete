from django.db import models
from django.test import TestCase

from safedelete import SOFT_DELETE_CASCADE
from safedelete.models import SafeDeleteMixin
from safedelete.tests.models import Article, Author, Category


class Press(SafeDeleteMixin):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article)


class PressNormalModel(models.Model):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article)


class SimpleTest(TestCase):
    def setUp(self):

        self.authors = (
            Author.objects.create(),
            Author.objects.create(),
            Author.objects.create(),
        )

        self.categories = (
            Category.objects.create(name='category 0'),
            Category.objects.create(name='category 1'),
            Category.objects.create(name='category 2'),
        )

        self.articles = (
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[1], category=self.categories[1]),
            Article.objects.create(author=self.authors[2], category=self.categories[2]),
        )

        self.press = (
            Press.objects.create(name='press 0', article=self.articles[2])
        )

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
