Django safedelete
=================

.. image:: https://travis-ci.org/makinacorpus/django-safedelete.png
    :target: https://travis-ci.org/makinacorpus/django-safedelete

.. image:: https://coveralls.io/repos/makinacorpus/django-safedelete/badge.png
    :target: https://coveralls.io/r/makinacorpus/django-safedelete


What is it ?
------------

For various reasons, you may want to avoid deleting objects from your database.

This Django application provides an abstract model, that allows you to transparently retrieve or delete your objects,
without having them deleted from your database.

You can choose what happens when you delete an object :
 - it can be masked from your database (soft delete, the default behavior)
 - it can be masked from your database and mask any dependent models. (cascading soft delete)
 - it can be normally deleted (hard delete)
 - it can be hard-deleted, but if its deletion would delete other objects, it will only be masked
 - it can be never deleted or masked from your database (no delete, use with caution)


Example
-------

.. code-block:: python

    # imports
    from safedelete.models import SafeDeleteModel
    from safedelete.models import HARD_DELETE_NOCASCADE

    # Models

    # We create a new model, with the given policy : Objects will be hard-deleted, or soft deleted if other objects would have been deleted too.
    class Article(SafeDeleteModel):
        _safedelete_policy = HARD_DELETE_NOCASCADE

        name = models.CharField(max_length=100)

    class Order(SafeDeleteModel):
        _safedelete_policy = HARD_DELETE_NOCASCADE

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
* Branch 0.4.x is compatible with django >= 1.8
* Branch 0.5.x is compatible with django >= 1.11

Current branch (0.5.x) has been tested with :

*  Django 1.11 using python 2.7 and python 3.4 to 3.6.
*  Django 2.0 using python 3.4 to 3.6.
*  Django 2.1 using python 3.5 to 3.7.


Installation
------------

Installing from pypi (using pip). ::

    pip install django-safedelete


Installing from github. ::

    pip install -e git://github.com/makinacorpus/django-safedelete.git#egg=django-safedelete

Add ``safedelete`` in your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        'safedelete',
        [...]
    ]


The application doesn't have any special requirement.


Configuration
-------------

In the main django settings you can activate the boolean variable ``SAFE_DELETE_INTERPRET_UNDELETED_OBJECTS_AS_CREATED``.
If you do this the ``update_or_create()`` function from django's standard manager class will return ``True`` for
the ``created`` variable if the object was soft-deleted and is now "revived".



Documentation
-------------

The documentation is available `here <http://django-safedelete.readthedocs.org>`_. Generate your own documentation using:

    tox -e docs


Licensing
---------

Please see the LICENSE file.

Contacts
--------

Please see the AUTHORS file.

.. image:: https://drupal.org/files/imagecache/grid-3/Logo_slogan_300dpi.png
    :target: http://www.makina-corpus.com
