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

Policies Delete Logic Customization
--------

Each of the policies has an overwritable function in case you need to customize a particular policy delete logic. The function per policy are as follows:

.. list-table::
    :widths: 15 10
    :header-rows: 1
    :align: center

    * - Policy
      - Overwritable Function
    * - SOFT_DELETE
      - soft_delete_policy_action
    * - HARD_DELETE
      - hard_delete_policy_action
    * - HARD_DELETE_NOCASCADE
      - hard_delete_cascade_policy_action
    * - SOFT_DELETE_CASCADE
      - soft_delete_cascade_policy_action    

    Example:
To add custom logic before or after the execution of the original delete logic of a model with the policy SOFT_DELETE you can overwrite the ``soft_delete_policy_action`` function as such:

.. code-block:: python
    def soft_delete_policy_action(self, **kwargs):
        # Insert here custom pre delete logic
        super().soft_delete_policy_action(**kwargs)
        # Insert here custom post delete logic


Fields uniqueness
-----------------

Because unique constraints are set at the database level, set `unique=True` on a field will also check uniqueness against soft deleted objects.
This can lead to confusion as the soft deleted objects are not visible by the user. This can be solved by setting a partial unique constraint that will only check uniqueness on non-deleted objects:

.. code-block:: python
    class Post(SafeDeleteModel):
        name = models.CharField(max_length=100)

        class Meta:
            constraints = [UniqueConstraint(fields=['name'], condition=Q(deleted__isnull=True), name='unique_active_name')]
