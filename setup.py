import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

with open('README.rst', 'r') as f_readme:
    with open('CHANGES', 'r') as f_changes:
        long_description = f_readme.read() + '\n\n' + f_changes.read()


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(here, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line.strip())
            if match:
                return match.groups()[0]
    raise RuntimeError("Unable to find version string.")


version = get_version('safedelete')

setup(
    name='django-safedelete',
    packages=find_packages(),
    version=version,
    description='Mask your objects instead of deleting them from your database.',
    long_description=long_description,
    author='Korantin Auguste',
    author_email='contact@palkeo.com',
    url='https://github.com/makinacorpus/django-safedelete',
    download_url='https://github.com/makinacorpus/django-safedelete/tarball/%s' % version,
    keywords=['django', 'delete', 'safedelete', 'softdelete'],
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
    ],
    license='BSD',
    install_requires=['Django'],
    include_package_data=True,
)
