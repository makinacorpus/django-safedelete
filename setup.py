import os
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()


setup(
    name = 'django-safedelete',
    packages = find_packages(),
    version = version,
    description = 'Mask your objects instead of deleting them from your database.',
    long_description = long_description,
    author = 'Korantin Auguste',
    author_email = 'contact@palkeo.com',
    url = 'https://github.com/makinacorpus/django-safedelete',
    download_url = 'https://github.com/makinacorpus/django-safedelete/tarball/%s' % version,
    keywords = ['django', 'delete', 'safedelete', 'softdelete'],
    classifiers = [
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 4 - Beta",
    ],
    license='BSD',
    requires=['Django (>= 1.3)'],
    include_package_data=True,
)
