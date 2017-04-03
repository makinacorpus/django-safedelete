from django.db import models
from safedelete import (DELETED_VISIBLE_BY_PK, HARD_DELETE,
                        HARD_DELETE_NOCASCADE, SOFT_DELETE)
from safedelete.managers import SafeDeleteManager
from safedelete.models import SafeDeleteModel


class Author(SafeDeleteModel):
    _safedelete_policy = HARD_DELETE_NOCASCADE


class CategoryManager(SafeDeleteManager):
    _safedelete_visibility = DELETED_VISIBLE_BY_PK


class Category(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    name = models.CharField(
        max_length=100,
        blank=True
    )


# Explicitly use SafeDeleteModel instead of SafeDeleteModel to test both
class Article(SafeDeleteModel):
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
