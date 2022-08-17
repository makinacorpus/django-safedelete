Django safedelete
=================

.. image:: https://github.com/makinacorpus/django-safedelete/workflows/Python%20application/badge.svg
    :target: https://github.com/makinacorpus/django-safedelete/actions?query=workflow%3A%22Python+application%22

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
* Branch 1.0.x, 1.1.x and 1.2.x are compatible with django >= 2.2
* Branch 1.3.x is compatible with django >= 3.2 and Python >= 3.7

Current branch (1.3.x) is tested with :

*  Django 3.2 using python 3.7 to 3.10.
*  Django 4.0 using python 3.8 to 3.10.
*  Django 4.1 using python 3.8 to 3.10.


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

By default, the field that indicates a database entry is soft-deleted is ``deleted``, however, you can override the field name
using the ``SAFE_DELETE_FIELD_NAME`` setting.

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
