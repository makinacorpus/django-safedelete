==================================================
Bonnes pratiques à l'écriture d'application Django
==================================================


Astuces générales
=================

 - Readme
 - Mettre un fichier `requirements.txt <http://www.pip-installer.org/en/latest/requirements.html>`_, avec toutes les bibliothèques dont a besoin l'application.
 - Vérifier le code avec pep8 et pyflakes (peut être fait automatiquement par Travis-CI).


Travis-CI
=========

Cf le ``.travis.yml`` du projet.


Code coverage
=============

Installer le paquet python « coverage ».

S'utilise comme ceci : ::

    coverage run quicktest.py application

Ce qui va créer un fichier ``.coverage``.

Ensuite, on peut afficher un rapport rapide avec ``coverage report``, ou même générer un répertoire
avec un rapport complet contenant le code source annoté avec ``coverage html``.

Si coveralls voit une couverture beaucoup plus faible que celle qu'on obtient en exécutant ``coverage`` en local,
il est possible de rajouter un fichier ``.coveragerc`` contenant : ::

    [run]
    source = répertoire_de_l'application


