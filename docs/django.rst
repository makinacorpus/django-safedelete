==================================================
Bonnes pratiques à l'écriture d'application Django
==================================================


Astuces générales
=================

 - Readme (en ReST)
 - Mettre un fichier `requirements.txt <http://www.pip-installer.org/en/latest/requirements.html>`_, avec toutes les bibliothèques dont a besoin l'application.
 - Vérifier le code avec pep8 et pyflakes (peut être fait automatiquement par Travis-CI).


Travis-CI
=========

::

    language: python

    python:
        - 2.6
        - 2.7
        - 3.2
        - 3.3

    env:
        - DJANGO_VERSION=1.3
        - DJANGO_VERSION=1.4
        - DJANGO_VERSION=1.5

    install: 
        # This is a dependency of our Django test script
        - pip install argparse --use-mirrors

        # Install the dependencies of the app itself
        - pip install -r requirements.txt --use-mirrors

        - pip install -q Django==$DJANGO_VERSION --use-mirrors

        - pip install coverage

        - pip install pep8 --use-mirrors
        - pip install pyflakes --use-mirrors

    before_script:
        - "pep8 --ignore=E501 safedelete"
        - pyflakes safedelete

    script:
        - coverage run quicktest.py safedelete

    after_success:
        - pip install coveralls
        - coveralls

    # We need to exclude old versions of Django for tests with python 3.
    matrix:
        exclude:
            - python: 3.2
              env: DJANGO_VERSION=1.3
            - python: 3.3
              env: DJANGO_VERSION=1.3
            - python: 3.2
              env: DJANGO_VERSION=1.4
            - python: 3.3
              env: DJANGO_VERSION=1.4


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


