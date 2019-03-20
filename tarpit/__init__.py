# coding:utf-8
"""Library Module."""
import os
import shutil
import sys
import subprocess
import argparse

from tornado import ioloop, gen
from tornado.web import Application
from tornado.options import options
from tornado.log import enable_pretty_logging
import yaml

from tarpit.config import CONFIG as O_O
from tarpit.web import ROUTES, recursive_import
# from tarpit.task import CeleryConfig, assemble_celery_cmd
from tarpit.utils import json_encoder


def set_dependence(module):
    recursive_import(module.__spec__.submodule_search_locations,
                     module.__name__)


def generate(dst):
    src = os.path.join(os.path.dirname(__file__), 'templates')
    shutil.copytree(src, dst)


def serve():
    enable_pretty_logging()

    for r in ROUTES:
        print(f'{r[0]:30s} {r[1]}')

    app = Application(handlers=ROUTES, **O_O.application)
    app.listen(O_O.server.port, **O_O.httpserver)

    O_O.show()
    print('\nstart listen...')
    ioloop.IOLoop.instance().start()


def main():
    sys.path.append(os.getcwd())

    parser = argparse.ArgumentParser(description='Tarpit commend line tools.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    subparsers.add_parser('serve')

    worker_parser = subparsers.add_parser('worker')
    # cc = CeleryConfig()
    # worker_parser.add_argument(
    #     '-q',
    #     '--queue',
    #     type=str,
    #     choices=[*cc.queue_list],
    #     help='Run worker instance.')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('directory', type=str, help='target directory.')

    params = parser.parse_args()

    if params.command != 'create':
        import mappers
        import services
        import controllers
        import collection
        set_dependence(collection)
        set_dependence(mappers)
        set_dependence(services)
        set_dependence(controllers)

    if params.command == 'serve':
        serve()
    elif params.command == 'worker':
        print('runworker')
    elif params.command == 'create':
        if os.path.exists(params.directory):
            parser.error('directory exists')
        generate(params.directory)
    else:
        parser.error('No valid options.')