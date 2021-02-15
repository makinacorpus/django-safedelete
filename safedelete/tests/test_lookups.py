from django.db import models
from django.test import TestCase

from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from safedelete.tests.models import Article, Author


class PressLookup(SafeDeleteModel):
    name = models.CharField(max_length=200)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class InLookupTest(TestCase):
    """
    Test cases for filtering safe delete models with the `in` ORM lookup.
    """

    def setUp(self):
        self.authors = (
            Author.objects.create(),
            Author.objects.create(),
            Author.objects.create(),
        )

        self.articles = (
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[1]),
            Article.objects.create(author=self.authors[2]),
        )

        self.press = (
            PressLookup.objects.create(name='press 0', article=self.articles[0]),
            PressLookup.objects.create(name='press 1', article=self.articles[1]),
            PressLookup.objects.create(name='press 2', article=self.articles[2]),
        )

    def test_filter_with_in(self):
        """
        Issue https://github.com/makinacorpus/django-safedelete/issues/101

        Using a SafeDeleteQueryset as the argument to a filters `in` lookup only works if the queryset is
          evaluated. i.e. Press.objects.filter(article__in=list(articles))
        """
        self.articles[0].delete(force_policy=SOFT_DELETE)
        self.articles[1].delete(force_policy=SOFT_DELETE)

        articles = Article.objects.filter()
        press = PressLookup.objects.filter(article__in=articles)

        self.assertEqual(press.count(), 1)
