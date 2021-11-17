=======================
Handling administration
=======================

Model admin
-----------

.. py:module:: safedelete.admin

Deleted objects will also be hidden in the admin site by default. A ``ModelAdmin`` abstract class is provided to give access to deleted objects.

An undelete action is provided to undelete objects in bulk. The ``deleted`` attribute is also excluded from editing by default.

You can use the ``highlight_deleted`` method to show deleted objects in red in the admin listing.

You also have the option of using ``highlight_deleted_field`` which is similar to ``highlight_deleted``, but allows you to specify a field for sorting and representation. Whereas ``highlight_deleted`` uses your object's ``__str__`` function to represent the object, ``highlight_deleted_field`` uses the value from your object's specified field.

To use ``highlight_deleted_field``, add "highlight_deleted_field" to your list filters (as a string, seen in the example below), and set `field_to_highlight = "desired_field_name"` (also seen below). Then you should also set its short description (again, see below).

.. autoclass:: SafeDeleteAdmin
