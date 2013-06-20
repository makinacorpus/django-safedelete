=================
Django safedelete
=================

What is it ?
------------

In a lot of projects, you don't want to delete objects from your database :
 - You may want to have the same behaviour as Django, and delete objects in cascade… But keeping them in your database.
 - Or perhaps you don't want to delete objects in cascade, so you just want to make them disappear without breaking anything.
 - Maybe you want to delete objects permanently, but if an object would delete other objects in cascade, you want to keep it in database.

This application can provide you mixins from which your objects will heritate…

Documentation
-------------

::
    
    class Article(SafeDeleteMixin):
        ...

Installation
------------

Licensing
---------

Please see the file LICENSE.

Contacts
--------

Please see the file AUTHORS.
