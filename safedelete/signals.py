from django.db.models.signals import ModelSignal

post_softdelete = ModelSignal(providing_args=["instance", "using"], use_caching=True)
post_undelete = ModelSignal(providing_args=["instance", "using"], use_caching=True)
