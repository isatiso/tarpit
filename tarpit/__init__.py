# coding:utf-8
"""Library Module."""
import os
import argparse
import unittest

from .command import serve, generate
from .test import get_tests

def main():

    parser = argparse.ArgumentParser(description='Tarpit commend line tools.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    subparsers.add_parser('serve')

    subparsers.add_parser('test')

    _worker_parser = subparsers.add_parser('worker')

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

    if params.command == 'serve':
        serve()
    elif params.command == 'worker':
        print('runworker')
    elif params.command == 'create':
        if os.path.exists(params.directory):
            parser.error('directory exists')
        generate(params.directory)
    elif params.command == 'test':
        suite = unittest.TestLoader().loadTestsFromTestCase(get_tests())
        unittest.TextTestRunner().run(suite)
    else:
        parser.error('No valid options.')