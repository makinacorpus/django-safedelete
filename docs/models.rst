=====
Model
=====

Built-in model
--------------

.. automodule:: safedelete.models
    :members:


Policies
--------

You can change the policy of your model by setting its ``_safedelete_policy`` attribute.
The different policies are:

.. py:data:: HARD_DELETE

    This will delete objects from the database if you call the delete() method.
    So, there is no difference with « normal » models, but you can still manually mask them from the database,
    by example by using ``obj.delete(force_policy=SOFT_DELETE)``.


.. py:data:: SOFT_DELETE

    This will make the objects be automatically masked (and not deleted), when you call the delete() method.
    They will NOT be masked in cascade.

.. py:data:: SOFT_DELETE_CASCADE

    This will make the objects be automatically masked (and not deleted) and all related objects, when you call the delete() method.
    They will be masked in cascade.

.. py:data:: HARD_DELETE_NOCASCADE

    This policy will:
     - Delete the object from database if no objects depends on it (e.g. no objects would have been deleted in cascade).
     - Mask the object if it would have deleted other objects with it.

.. py:data:: NO_DELETE

    This will keep the objects from being masked or deleted from your database. The only way of removing objects will be by using raw SQL.
