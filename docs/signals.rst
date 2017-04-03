=======
Signals
=======

.. py:module:: safedelete.signals


Signals
-------

There are two signals available. Please refer to the `Django signals <https://docs.djangoproject.com/en/dev/topics/signals/>`_ documentation on how to use them.

.. py:data:: safedelete.signals.pre_softdelete

Sent before an object is soft deleted.

.. py:data:: safedelete.signals.post_softdelete

Sent after an object has been soft deleted.

.. py:data:: safedelete.signals.post_undelete

Sent after a deleted object is restored.
