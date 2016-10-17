===============
Creating models
===============

.. py:module:: safedelete.models

To create your safedelete-ready models, you have to make them inherit from an abstract model.

You can create this abstract model by calling the function :py:func:`safedelete_mixin_factory` (in :py:mod:`safedelete.models`) :

.. autofunction:: safedelete_mixin_factory


There is also a shortcut available if you want to have simple soft-deletable objects :

.. py:data:: safedelete.shortcuts.SoftDeleteMixin

    This is a ready-to-use base model, obtained by calling ``safedelete_mixin_factory(SOFT_DELETE)``.


Policies
--------

The different policies are :

.. py:data:: HARD_DELETE

    This will delete objects from the database if you call the delete() method.
    So, there is no difference with « normal » models, but you can still manually mask them from the database,
    by example using ``obj.delete(force_policy=SOFT_DELETE)``.


.. py:data:: SOFT_DELETE

    This will make the objects be automatically masked (and not deleted), when you call the delete() method.
    They will NOT be masked in cascade.

.. py:data:: HARD_DELETE_NOCASCADE

    This policy will :
     - Delete the object from database if no objects depends on it (e.g. no objects would have been deleted in cascade).
     - Mask the object if it would have deleted other objects with it.

.. py:data:: NO_DELETE

    This will keep the objects from being masked or deleted from your database. The only way of removing objects will be by using raw SQL.


Visibility
----------

You can also give a ``visibility`` argument, useful to choose how you can see the objects that are "masked" :

.. py:data:: DELETED_INVISIBLE

    This is the default visibility.

    The objects marked as deleted will be visible in one case : If you access them directly using a OneToOne or a ForeignKey
    relation.

    For example, if you have an article with a masked author, you can still access the author using ``article.author``.
    If the article is masked, you are not able to access it using reverse relationship : ``author.article_set`` will not contain
    the masked article.


.. py:data:: DELETED_VISIBLE_BY_FIELD

    This policy is like :py:data:`DELETED_INVISIBLE`, except that you can still access a deleted object if you call the ``get()`` or ``filter()``
    function, passing it the ``pk`` parameter. The field is configurable, check :py:data:`VISIBLE_BY_FIELD`.

    So, deleted objects are still available if you access them directly by their primary key.

.. py:data:: VISIBLE_BY_FIELD 

    The :py:data:`DELETED_VISIBLE_BY_FIELD`, is configurable by adding this variable to your django settings.
    The field chosen should be a unique field. e.g: You can assign it in the settings as ``uuid`` field instead.
