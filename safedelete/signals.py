from django.db.models.signals import ModelSignal

pre_softdelete = ModelSignal(use_caching=True)
post_softdelete = ModelSignal(use_caching=True)
post_undelete = ModelSignal(use_caching=True)
