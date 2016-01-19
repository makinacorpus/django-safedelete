from distutils.version import LooseVersion

import django
try:
    from django.db.models.signals import ModelSignal as Signal
except ImportError:
    from django.dispatch import Signal


if LooseVersion(django.get_version()) < LooseVersion('1.6'):
    post_softdelete = Signal(providing_args=["instance", "using"])
    post_undelete = Signal(providing_args=["instance", "using"])
else:
    post_softdelete = Signal(providing_args=["instance", "using"], use_caching=True)
    post_undelete = Signal(providing_args=["instance", "using"], use_caching=True)
