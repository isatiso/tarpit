#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='tarpit',
    version='0.0.4',
    author='plank',
    author_email='sieglive@gmail.com',
    url='https://lazor.cn',
    description=u'吃枣药丸',
    license="GPLv3+",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'alembic==1.0.7',
        'celery==4.2.1',
        'gevent==1.4.0',
        'motor==2.0.0',
        'PyJWT==1.7.1',
        'pymongo==3.7.2',
        'PyMySQL==0.9.3',
        'PyYAML==5.1',
        'redis==3.2.0',
        'requests==2.21.0',
        'SQLAlchemy==1.2.18',
        'tornado==5.1.1',
        'cryptography==2.6.1',
    ],
    entry_points={'console_scripts': ['tarpit=tarpit:main']},
)
