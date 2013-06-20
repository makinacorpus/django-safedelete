from django.db import models
from django.test import TestCase

from .models import safedelete_mixin_factory


# MODELS (FOR TESTING)


class Author(safedelete_mixin_factory(policy_soft_delete=True, policy_hard_delete=True)):
    name = models.CharField(max_length=200)

class Article(safedelete_mixin_factory(policy_soft_delete=False, policy_hard_delete=True)):
    name = models.CharField(max_length=200)
    author = models.ForeignKey(Author, null=True, default=None)

class Category(safedelete_mixin_factory(policy_soft_delete=True, policy_hard_delete=False)):
    name = models.CharField(max_length=200)


# TESTS


class SimpleTest(TestCase):
    def setUp(self):

        self.authors = (
            Author(name='author 0'),
            Author(name='author 1'),
            Author(name='author 2'),
        )

        self.articles = (
            Article(name='article 0'),
            Article(name='article 1', author=self.authors[1]),
            Article(name='article 2', author=self.authors[2]),
        )

        for i in self.authors + self.articles:
            i.save()

    def test_softdelete_noharddelete(self):
        pass
