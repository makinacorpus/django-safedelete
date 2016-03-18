===============
Creating models
===============

.. py:module:: safedelete.models

To create your safedelete-ready models, you have to make them inherit from an abstract model.

.. autoclass:: SafeDeleteMixin

The ``deleted`` attribute is a DateTimeField set to the moment the object was deleted.

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

.. py:data:: HARD_DELETE_NOCASCADE

    This policy will:
     - Delete the object from database if no objects depends on it (e.g. no objects would have been deleted in cascade).
     - Mask the object if it would have deleted other objects with it.

.. py:data:: NO_DELETE

    This will keep the objects from being masked or deleted from your database. The only way of removing objects will be by using raw SQL.


Visibility
----------

A custom manager is used to determine which objects should be included in the querysets.

.. autoclass:: SafeDeleteManager

If you want to change which objects are "masked", you can set the ``_safedelete_visibility``
attribute of the manager to one of the following:

.. py:data:: DELETED_INVISIBLE

    This is the default visibility.

    The objects marked as deleted will be visible in one case : If you access them directly using a OneToOne or a ForeignKey
    relation.

    For example, if you have an article with a masked autor, you can still access the author using ``article.author``.
    If the article is masked, you are not able to access it using reverse relationship : ``author.article_set`` will not contain
    the masked article.


.. py:data:: DELETED_VISIBLE_BY_PK

    This policy is like :py:data:`DELETED_INVISIBLE`, except that you can still access a deleted object if you call the ``get()`` or ``filter()``
    function, passing it the ``pk`` parameter.

    So, deleted objects are still available if you access them directly by their primary key.


Signals
-------

There are two signals available. Please refer on Django signals documentation on how to use them.

.. py:data:: safedelete.signals.post_softdelete

Sent after an object has been soft deleted.

.. py:data:: safedelete.signals.post_undelete

Sent after a deleted object is restored.
