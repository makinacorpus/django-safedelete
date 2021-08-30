========
Managers
========

Built-in managers
-----------------

.. automodule:: safedelete.managers
    :members:

Visibility
----------

A custom manager is used to determine which objects should be included in the querysets.

.. autoclass:: SafeDeleteManager
    :noindex:

If you want to change which objects are "masked", you can set the ``_safedelete_visibility``
attribute of the manager to one of the following:

.. py:data:: DELETED_INVISIBLE

    This is the default visibility.

    The objects marked as deleted will be visible in one case : If you access them directly using a OneToOne or a ForeignKey
    relation.

    For example, if you have an article with a masked author, you can still access the author using ``article.author``.
    If the article is masked, you are not able to access it using reverse relationship : ``author.article_set`` will not contain
    the masked article.


.. py:data:: DELETED_VISIBLE_BY_FIELD

    This policy is like :py:data:`DELETED_INVISIBLE`, except that you can still access a deleted object if you call the ``get()`` or ``filter()``
    function, passing it the default field ``pk`` parameter. Configurable through the `_safedelete_visibility_field` attribute of the manager.

    So, deleted objects are still available if you access them directly by this field.
