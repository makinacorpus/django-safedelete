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

    This policy will:
        - Hard delete objects from the database if you call the :py:func:`delete()` method.

            There is no difference with « normal » models, but you can still manually mask them from the database, for example by using ``obj.delete(force_policy=SOFT_DELETE)``.


.. py:data:: SOFT_DELETE

    This policy will:

    This will make the objects be automatically masked (and not deleted), when you call the delete() method.
    They will NOT be masked in cascade.

.. py:data:: SOFT_DELETE_CASCADE

    This policy will:

    This will make the objects be automatically masked (and not deleted) and all related objects, when you call the delete() method.
    They will be masked in cascade.

.. py:data:: HARD_DELETE_NOCASCADE

    This policy will:
        - Delete the object from database if no objects depends on it (e.g. no objects would have been deleted in cascade).
        - Mask the object if it would have deleted other objects with it.

.. py:data:: NO_DELETE

    This policy will:
        - Keep the objects from being masked or deleted from your database. The only way of removing objects will be by using raw SQL.


 Fields
------

 When you use custom ``through`` model for M2M relations, you may want
that related manager return only not-deleted relations. If so, you may want
to use ``safedelete.fields.SafeDeleteManyToManyField``.

 You still will be able to retrieve deleted instances for intermediate model using
it's manager.
