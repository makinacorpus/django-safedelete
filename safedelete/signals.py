from django.db.models.signals import ModelSignal


post_soft_delete = ModelSignal(
    providing_args=["instance", "using"], use_caching=True)
post_soft_create = ModelSignal(
    providing_args=["instance", "using"], use_caching=True)
