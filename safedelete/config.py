from django.conf import settings

HARD_DELETE = 0
SOFT_DELETE = 1
SOFT_DELETE_CASCADE = 2
HARD_DELETE_NOCASCADE = 3
NO_DELETE = 4

DELETED_INVISIBLE = 10
DELETED_VISIBLE_BY_FIELD = DELETED_VISIBLE_BY_PK = 11
DELETED_ONLY_VISIBLE = 12
DELETED_VISIBLE = 13
FIELD_NAME = getattr(settings, 'SAFE_DELETE_FIELD_NAME', 'deleted')

# If you have a boolean field to be marked when you do safedelete, set HAS_BOOLEAN_FIELD to True.
# And configure the boolean field name.
HAS_BOOLEAN_FIELD = getattr(settings, 'SAFE_DELETE_HAS_BOOLEAN_FIELD', False)
BOOLEAN_FIELD_NAME = getattr(settings, 'SAFE_DELETE_BOOLEAN_FIELD_NAME', 'is_deleted')

# IF you would like to filter for deleted elements using the boolean field instead of checking if the datetime field
# is not set, set this variable to True.
# This is specially useful if you have indexes on the boolean field at DB level.
USE_BOOLEAN_FIELD = getattr(settings, 'SAFE_DELETE_USE_BOOLEAN_FIELD_TO_DO_LOGIC', False)
