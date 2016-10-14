from .models import safedelete_mixin_factory
from .utils import SOFT_DELETE, SOFT_DELETE_CASCADE


SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)
SoftDeleteCascadeMixin = safedelete_mixin_factory(SOFT_DELETE_CASCADE)
