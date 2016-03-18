from django.db.models.deletion import Collector
from django.db import router


HARD_DELETE = 0
SOFT_DELETE = 1
SOFT_DELETE_CASCADE = 2
HARD_DELETE_NOCASCADE = 3
NO_DELETE = 4

DELETED_INVISIBLE = 10
DELETED_VISIBLE_BY_PK = 11


def can_hard_delete(obj):
    collector = Collector(using=router.db_for_write(obj))
    collector.collect([obj])
    return not bool(collector.fast_deletes)
