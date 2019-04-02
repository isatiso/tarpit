# coding:utf-8
"""Convert YAML to Python Data."""
import sys
import os
import json

import yaml
from .utils import Arguments

_ENV = os.getenv('TARPIT_ENV', 'mypc')


class Configuration:
    """Config Module"""
    _instance = None

    def __new__(cls, **kwargs):
        if not cls._instance:
            cls._instance = super(Configuration, cls).__new__(cls)
            cls._instance.__init__(**kwargs)
        return cls._instance

    def __init__(self, filepath='settings/config.yml'):
        CONFIG_PATH = os.path.join(os.getcwd(), filepath)
        data = dict(error='Config File Not Found.')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config:
                data = yaml.load(config, Loader=yaml.FullLoader)
        except FileNotFoundError:
            pass

        self.data = Arguments(self.convert(data))

    def create(self):
        return self.data

    def convert(self, params):
        new_dict = dict()
        for key in params:
            if isinstance(params[key], dict):
                if _ENV in params[key]:
                    new_dict[key] = params[key][_ENV]
                else:
                    new_dict[key] = self.convert(params[key])
            else:
                new_dict[key] = params[key]
        return new_dict

    def __getattr__(self, name):
        return self.data.__getattr__(name)

    def show(self):
        sys.stdout.write('\nconfig:\n')
        json.dump(self.data.traverse(), sys.stdout, indent=4, sort_keys=True)
        sys.stdout.write('\n\n\n')
        sys.stdout.flush()


class ErrorCode():

    _code = {}

    def __init__(self, filepath='settings/status.yml'):
        STATUS_PATH = os.path.join(os.getcwd(), filepath)
        code_list = []
        try:
            with open(STATUS_PATH, 'r', encoding='utf-8') as config:
                code_list = yaml.load(config, Loader=yaml.FullLoader)
        except FileNotFoundError:
            pass

        if isinstance(code_list, list):
            for item in code_list:
                if 'code' not in item or 'msg' not in item:
                    raise KeyError('Wrong format of status')
                self._code[item.get('code')] = item.get('msg')

    def get_code(self, code, default=None):
        return self._code.get(code, default)


CONFIG = Configuration()
STATUS = ErrorCode()


def get_status_message(code):
    if code == -1:
        return None

    return STATUS.get_code(code, f'Unknown status {code}.')
