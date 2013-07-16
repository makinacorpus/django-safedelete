Django safedelete
=================

.. image:: https://travis-ci.org/makinacorpus/django-safedelete.png
    :target: https://travis-ci.org/makinacorpus/django-safedelete

.. image:: https://coveralls.io/repos/makinacorpus/django-safedelete/badge.png
    :target: https://coveralls.io/r/makinacorpus/django-safedelete


What is it ?
------------

For various reasons, you may want to avoid deleting objects from your database.

This Django application provides a model mixin, that allows you to transparently retrieve or delete your objects,
without having them deleted from your database.

You can choose what happens when you delete an object :
 - it can be masked from your database (soft delete)
 - it can be normally deleted (hard delete)
 - it can be hard-deleted, but if its deletion would delete other objects, it will only be masked


Example
-------

.. code-block:: python

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


Installation
------------

::

    pip install django-safedelete

The application doesn't have any special requirement.

It have been tested with Django 1.3, 1.4 and 1.5, using python 2.6 and 2.7.
It is also compatible with python 3, using Django 1.5.


Documentation
-------------

The documentation is available `here <http://django-safedelete.readthedocs.org>`_.


Licensing
---------

Please see the LICENSE file.

Contacts
--------

Please see the AUTHORS file.

.. image:: https://drupal.org/files/imagecache/grid-3/Logo_slogan_300dpi.png
    :target: http://www.makina-corpus.com

