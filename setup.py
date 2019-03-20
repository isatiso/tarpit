#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='tarpit',
    version='0.0.3',
    author='plank',
    author_email='sieglive@gmail.com',
    url='https://lazor.cn',
    description=u'吃枣药丸',
    license="GPLv3+",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'tornado',
        'motor',
        'pymongo',
        'celery',
        'gevent',
        'sqlalchemy',
        'pymysql',
        'redis',
        'pyyaml',
        'requests',
        'alembic',
        'pyjwt',
        'cryptography',
    ],
    entry_points={'console_scripts': ['tarpit=tarpit:main']},
)
