from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db import models
from django.test import TestCase
from django.core.exceptions import FieldError

from safedelete import SOFT_DELETE, SOFT_DELETE_CASCADE
from safedelete.config import DELETED_BY_CASCADE_FIELD_NAME
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


class Section(SafeDeleteModel):
    title = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class Table(SafeDeleteModel):
    index = models.IntegerField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    vars()[DELETED_BY_CASCADE_FIELD_NAME] = None


class HardTable(models.Model):
    index = models.IntegerField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE)


class Image(SafeDeleteModel):
    index = models.IntegerField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE)


class PressNormalModel(models.Model):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)


class ParentGeneric(SafeDeleteModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    child = GenericForeignKey()


class ChildGeneric(SafeDeleteModel):
    parent = GenericRelation(
        ParentGeneric, related_name="childs"
    )


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

        self.sections = (
            Section.objects.create(title='Abstract', article=self.articles[2]),
            Section.objects.create(title='Methods', article=self.articles[2]),
            Section.objects.create(title='Results', article=self.articles[2]),
        )

        self.tables = (
            Table.objects.create(index=1, section=self.sections[1]),
            Table.objects.create(index=1, section=self.sections[2]),
            Table.objects.create(index=1, section=self.sections[2]),
        )

        self.images = (
            Image.objects.create(index=1, section=self.sections[1]),
            Image.objects.create(index=1, section=self.sections[2]),
            Image.objects.create(index=1, section=self.sections[2]),
        )

    def test_soft_delete_cascade(self):
        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)

        output = self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 2)
        self.assertEqual(Author.all_objects.count(), 3)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.all_objects.count(), 3)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Press.all_objects.count(), 1)

        expected_output_dict = {
            'safedelete.Article': 1,
            'safedelete.Press': 1,
            'safedelete.Section': 3,
            'safedelete.Table': 3,
            'safedelete.Image': 3,
            'safedelete.Author': 1,
        }
        self.assertEqual(output, (12, expected_output_dict))

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
            delete_article_mock.return_value = (1, {'safedelete.Article': 1})
            self.authors[1].delete(force_policy=SOFT_DELETE_CASCADE)

            # delete_article_mock.assert_called_once doesn't work on py35
            self.assertEqual(delete_article_mock.call_count, 1)

    def test_undelete_with_soft_delete_cascade_policy(self):
        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)
        output = self.authors[2].undelete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Author.objects.count(), 3)
        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)

        expected_output_dict = {
            'safedelete.Article': 1,
            'safedelete.Press': 1,
            'safedelete.Section': 3,
            'safedelete.Image': 3,
            'safedelete.Author': 1,
        }
        self.assertEqual(output, (9, expected_output_dict))

    def test_undelete_with_cascade_control_class_included(self):
        self.sections[1].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Section.objects.count(), 2)
        self.assertEqual(Image.objects.count(), 2)

        self.authors[2].delete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Press.objects.count(), 0)
        self.assertEqual(Section.objects.count(), 0)
        self.assertEqual(Section.deleted_objects.filter(**{DELETED_BY_CASCADE_FIELD_NAME: True}).count(), 2)

        self.authors[2].undelete(force_policy=SOFT_DELETE_CASCADE)

        self.assertEqual(Article.objects.count(), 3)
        self.assertEqual(Press.objects.count(), 1)
        self.assertEqual(Section.objects.filter(**{DELETED_BY_CASCADE_FIELD_NAME: False}).count(), 2)
        self.assertEqual(Image.objects.count(), 2)
        self.assertEqual(self.sections[1], Section.deleted_objects.first())

    def test_safe_delete_cascade_control_attribute_overriding(self):

        with self.assertRaises(FieldError):
            Table.objects.filter(**{DELETED_BY_CASCADE_FIELD_NAME: False})

        HardTable.objects.create(index=1, section=self.sections[2])

        self.tables[2].delete()
        self.sections[2].delete(force_policy=SOFT_DELETE_CASCADE)
        self.sections[2].undelete(force_policy=SOFT_DELETE_CASCADE)
        self.assertEqual(Table.objects.count(), 1)
        self.tables[2].undelete()
        self.assertEqual(Table.objects.count(), 2)

    def test_safe_delete_cascade_generic_foreign_key(self):
        child = ChildGeneric.objects.create()
        ParentGeneric.objects.create(child=child)

        child.delete(force_policy=SOFT_DELETE_CASCADE)
        self.assertEqual(ChildGeneric.objects.count(), 0)
        self.assertEqual(ParentGeneric.objects.count(), 0)
        child.undelete(force_policy=SOFT_DELETE_CASCADE)
        self.assertEqual(ChildGeneric.objects.count(), 1)
        self.assertEqual(ParentGeneric.objects.count(), 1)
