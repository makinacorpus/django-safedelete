# flake8: noqa

from .config import (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK, DELETED_VISIBLE_BY_FIELD,
                     HARD_DELETE, HARD_DELETE_NOCASCADE, SOFT_DELETE, SOFT_DELETE_CASCADE,
                     NO_DELETE)

__all__ = [
    'HARD_DELETE',
    'SOFT_DELETE',
    'SOFT_DELETE_CASCADE',
    'HARD_DELETE_NOCASCADE',
    'NO_DELETE',
    'DELETED_INVISIBLE',
    'DELETED_VISIBLE_BY_PK',
    'DELETED_VISIBLE_BY_FIELD',
]

__version__ = "0.4.2"
default_app_config = 'safedelete.apps.SafeDeleteConfig'
