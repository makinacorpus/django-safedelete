=================
Django safedelete
=================

What is it ?
------------

For various reasons, you may want to avoid deleting objects from your database.

This Django application provides you with a base mixin for your models, that allow you transparently retrieve or delete your objects,
without having them deleted from your database.

You can choose what happens when you delete an object :
 - it can be masked from your database (soft delete), in cascade or not
 - it can be normally deleted (hard delete)
 - it can be hard-deleted, but if its deletion would delete other objects, it will only be masked


Example
-------

.. code:: python

    # Models

    # We create a new mixin, with the given policy : Objects will be hard-deleted, or soft deleted if other objects would have been deleted too.
    SafeDeleteMixin = safedelete_mixin_factory(HARD_DELETE_NOCASCADE)

    class Article(SafeDeleteMixin):
        name = models.CharField(max_length=100)

    class Order(SafeDeleteMixin):
        name = models.CharField(max_length=100)
        articles = models.ManyToManyField(Article)


    # Example of use

    >>> article1 = Article(name='article1')
    >>> article1.save()

    >>> article2 = Article(name='article2')
    >>> article2.save()

    >>> order = Order(name='order')
    >>> order.save()
    >>> order.articles.add(article1)

    # This article will be masked, but not deleted from the database as it is still referenced in an order.
    >>> article1.delete()

    # This article will be deleted from the database.
    >>> article2.delete()


Documentation
-------------

The documentation is available `here <http://django-safedelete.readthedocs.com>`_.

Installation
------------

Just install it.

Licensing
---------

Please see the file LICENSE.

Contacts
--------

Please see the file AUTHORS.
