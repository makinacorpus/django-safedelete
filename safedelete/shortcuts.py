from .models import safedelete_mixin_factory
from .utils import SOFT_DELETE


SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)
