# flake8: noqa

from .utils import (HARD_DELETE, SOFT_DELETE, HARD_DELETE_NOCASCADE,
                    DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK)
from .models import safedelete_mixin_factory
from .managers import safedelete_manager_factory

__all__ = ['safedelete_manager_factory',
           'safedelete_mixin_factory',
           'HARD_DELETE', 'SOFT_DELETE',
           'HARD_DELETE_NOCASCADE',
           'DELETED_INVISIBLE',
           'DELETED_VISIBLE_BY_PK']


pkg_resources = __import__('pkg_resources')
distribution = pkg_resources.get_distribution('django-safedelete')

#: Module version, as defined in PEP-0396.
__version__ = distribution.version
