=======================
Handling administration
=======================

Model admin
-----------

.. py:module:: safedelete.admin

Deleted objects will also be hidden in the admin site by default. A ``ModelAdmin`` abstract class is provided to give access to deleted objects.

An undelete action is provided to undelete objects in bulk. The ``deleted`` attribute is also excluded from editing by default.

You can use the ``highlight_deleted`` method to show deleted objects in red in the admin listing.

.. autoclass:: SafeDeleteAdmin
