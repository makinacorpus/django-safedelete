from distutils.core import setup

with open('README.rst', 'r') as f:
    long_description = f.read()

version = "0.1.1"

setup(
    name = 'django-safedelete',
    packages = ['django-safedelete'],
    version = version,
    description = 'Make you objects invisible instead of deleting them from your database.',
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
)
