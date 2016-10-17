from django.conf import settings

# Should be unique field
VISIBLE_BY_FIELD = getattr(settings, "VISIBLE_BY_FIELD", "pk")
