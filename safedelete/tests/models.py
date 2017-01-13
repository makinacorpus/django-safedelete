from django.db import models

from safedelete import DELETED_VISIBLE_BY_PK
from safedelete import HARD_DELETE
from safedelete import HARD_DELETE_NOCASCADE
from safedelete import SOFT_DELETE
from safedelete.managers import SafeDeleteManager
from safedelete.models import SafeDeleteMixin


class Author(SafeDeleteMixin):
    _safedelete_policy = HARD_DELETE_NOCASCADE


class CategoryManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_PK


class Category(SafeDeleteMixin):
    _safedelete_policy = SOFT_DELETE

    name = models.CharField(
        max_length=100,
        blank=True
    )

    objects = CategoryManager()


class Article(SafeDeleteMixin):
    _safedelete_policy = HARD_DELETE

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        default=None
    )
