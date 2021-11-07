from django.db import models
from django.test import TestCase

from safedelete import SOFT_DELETE, SOFT_DELETE_CASCADE
from safedelete.models import SafeDeleteModel
from safedelete.signals import pre_softdelete
from safedelete.tests.models import Article, Author, Category

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch  # for python 2 supporting


class Press(SafeDeleteModel):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class PressNormalModel(models.Model):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)


class CustomAbstractModel(SafeDeleteModel):

    class Meta:
        abstract = True


class ArticleView(CustomAbstractModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    article = models.ForeignKey(Article, on_delete=models.CASCADE)


def pre_softdelete_article(sender, instance, *args, **kwargs):
    # Related objects should not be SET before instance was deleted
    assert instance.pressnormalmodel_set.count() == 1


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
        self.assertEqual(Author.all_objects.count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.all_objects.count(), 1)

    def test_soft_delete_cascade_with_normal_model(self):
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        pre_softdelete.connect(pre_softdelete_article, Article)
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        pre_softdelete.disconnect(pre_softdelete_article, Article)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.all_objects.count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.all_objects.count(), 1)
        self.assertEqual(PressNormalModel.objects.count(), 1)

    def test_soft_delete_cascade_with_set_null(self):
        PressNormalModel.article.field.null = True
        PressNormalModel.article.field.remote_field.on_delete = models.SET_NULL
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        pre_softdelete.connect(pre_softdelete_article, Article)
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        pre_softdelete.disconnect(pre_softdelete_article, Article)

        self.assertEqual(PressNormalModel.objects.first().article, None)

    def test_soft_delete_cascade_with_set_default(self):
        PressNormalModel.article.field.default = self.articles[1]
        PressNormalModel.article.field.remote_field.on_delete = models.SET_DEFAULT
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        pre_softdelete.connect(pre_softdelete_article, Article)
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        pre_softdelete.disconnect(pre_softdelete_article, Article)

        self.assertEqual(PressNormalModel.objects.first().article, self.articles[1])

    def test_soft_delete_cascade_with_set(self):
        PressNormalModel.article.field.remote_field.on_delete = models.SET(self.articles[0])
        PressNormalModel.objects.create(name='press 0', article=self.articles[2])
        pre_softdelete.connect(pre_softdelete_article, Article)
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        pre_softdelete.disconnect(pre_softdelete_article, Article)

        self.assertEqual(PressNormalModel.objects.first().article, self.articles[0])

    def test_soft_delete_cascade_with_abstract_model(self):
        ArticleView.objects.create(article=self.articles[2])

        self.articles[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)

        self.assertEqual(ArticleView.objects.count(), 0)
        self.assertEqual(ArticleView.all_objects.count(), 1)

    def test_soft_delete_cascade_deleted(self):
        self.articles[0].delete(force_policy=SOFT_DELETE)
        self.assertEqual(self.authors[1].article_set.count(), 1)

        with patch('safedelete.tests.models.Article.delete') as delete_article_mock:
            self.authors[1].delete(force_policy=SOFT_DELETE_CASCADE)

            # delete_article_mock.assert_called_once doesn't work on py35
            self.assertEqual(delete_article_mock.call_count, 1)

    def test_undelete_with_soft_delete_cascade_policy(self):
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        self.authors[2].undelete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)
