# coding: utf-8
"""
wax-mock
~~~~~~~~
Mock server with Swagger OpenAPI3 JSON
Setup
-----
.. code-block:: bash
    > pip install wax-mock
    > wax swagger_api.json

"""

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path
from setuptools.command.install import install
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')
version = str(ast.literal_eval(
    _version_re.search(
        open('wax/__init__.py').read()
    ).group(1)
))
here = path.abspath(path.dirname(__file__))


class MyInstall(install):
    def run(self):
        print("-- installing... --")
        install.run(self)

setup(
        name = 'wax-mock',
        version=version,
        description='Mock server with Swagger OpenAPI3 JSON',
        long_description='\npip install wax-mock\n\n'
                         'wax swagger_api.json',
        url='https://pypi.python.org/project/wax-mock',
        author='qorzj',
        author_email='inull@qq.com',
        license='MIT',
        platforms=['any'],

        classifiers=[
            ],
        keywords='mock swagger openapi openapi3',
        packages = ['wax', 'wax.lessweb', 'wax.lessweb.plugin'],
        install_requires=[
            'jsonschema',
            'strict-rfc3339',
            'rfc3987',
            'aiohttp',
            'aiohttp_wsgi',
            'requests',
            'typing_inspect',
            'typing_extensions',
            'redis',
            'hiredis',
            'Mako',
        ],
        cmdclass={'install': MyInstall},
        entry_points={
            'console_scripts': [
                'wax = wax.main:entrypoint'
            ],
        },
    )
