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
 - it can be never deleted or masked from your database (no delete, use with caution)


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


Compatibilities
---------------

* Branch 0.2.x is compatible with django >= 1.2
* Branch 0.3.x is compatible with django >= 1.4

Current branch (0.3.x) has been tested with :

*  Django 1.4, using python 2.6 and 2.7.
*  Django 1.5 and 1.6, using python 2.6, 2.7 and 3.x.
*  Django 1.7 using python 2.7 and python 3.x.
*  Django 1.8 using python 2.7 and python 3.x.
*  Django 1.9 using python 2.7 and python 3.x.



Installation
------------

Installing from pypi (using pip). ::

    pip install django-safedelete


Installing from github. ::

    pip install -e git://github.com/makinacorpus/django-safedelete.git#egg=django-safedelete


The application doesn't have any special requirement.


Documentation
-------------

The documentation is available `here <https://django-safedelete.readthedocs.io>`_.


Licensing
---------

Please see the LICENSE file.

Contacts
--------

Please see the AUTHORS file.

.. image:: https://drupal.org/files/imagecache/grid-3/Logo_slogan_300dpi.png
    :target: http://www.makina-corpus.com

