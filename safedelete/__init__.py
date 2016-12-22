# flake8: noqa

from .config import (DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK, HARD_DELETE,
                     HARD_DELETE_NOCASCADE, SOFT_DELETE)

__all__ = ['HARD_DELETE', 'SOFT_DELETE',
           'HARD_DELETE_NOCASCADE',
           'DELETED_INVISIBLE',
           'DELETED_VISIBLE_BY_PK']

__version__ = "0.4.0"
default_app_config = 'safedelete.apps.SafeDeleteConfig'
