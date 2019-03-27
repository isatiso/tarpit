import re
import os
import types
import json
from unittest import TestCase

import requests
import yaml

from .utils import Arguments

from pprint import pprint


def pretty_print(prepared_request):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    method = prepared_request.method
    url = prepared_request.url
    headers = '\n'.join(
        f'{k}: {v}' for k, v in prepared_request.headers.items())
    body = prepared_request.body
    print('-----------START-----------')
    print(f'{method} {url}\n{headers}\n\n{body}')
    print('-----------ENDED-----------')


def get_tests():

    attrs = dict()

    attrs['checker'] = re.compile(r'(\$[a-z]+)( *: *)([^;]*)')
    attrs['number'] = re.compile(r'^[0-9]+$')
    attrs['word'] = re.compile(r'^\w+$')
    attrs['method'] = re.compile(r'(GET|POST|PUT|DELETE|HEAD|OPTIONS)')
    attrs['url'] = re.compile(r'(/[a-zA-Z0-9\-_]+)*/?')
    requests_data = read_config('test/requests.yml')
    env = Arguments(read_config('test/env.yml'))
    settings = Arguments(read_config('test/settings.yml'))

    if not isinstance(requests_data, list):
        raise ValueError('Wrong formatter.')

    attrs['requests_data'] = requests_data
    attrs['env'] = env
    attrs['settings'] = settings

    class_dict = {
        f'test_request_{i}': lambda self: TestItem(self, item, self.env).run()
        for i, item in enumerate(requests_data)
    }

    return type('TarpitTest', (TestCase,), dict(attrs, **class_dict))


def read_config(path):
    path = os.path.join(os.getcwd(), path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        data = dict()

    return data


class TestItem():

    def __init__(self, tc, info, env):
        self.tc = tc
        self.info = info
        self.env = EnvRender(env)
        self.request = RequestBuilder()

    def run(self):
        info = self.env.render(self.info)
        info = Arguments(info)
        self.request.build(info.request)
        response = self.request.send()

        res_dict = dict(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.json())

        checker = Checker(info.response, self.tc)
        checker.check(res_dict)

        if info.set_env:
            for k, v in info.set_env.items():
                self.set_env(k, v, res_dict)

        print(self.env)

    def set_env(self, name, value_path, resp):
        value_path_list = list(reversed(value_path.split('.')))
        value = self.find_value(value_path_list, resp)
        self.env.update(name, value)

    def find_value(self, target, data):
        if not target:
            return None
        cur = target.pop()
        if isinstance(data, dict):
            thisnode = data.get(cur)
        else:
            cur = int(cur)
            thisnode = data[cur]

        if not target:
            return thisnode

        if not isinstance(thisnode, (dict, list)):
            raise TypeError(
                f'Wrong type "{type(thisnode).__name__}" of node under key "{cur}"'
            )
        else:
            return self.find_value(target, thisnode)


class EnvRender():

    def __init__(self, env):
        self.env = env

    def update(self, k, v):
        self.env[k] = v

    def render(self, data):
        if isinstance(data, list):
            raise TypeError('item need to be a dict')
        return self._render_env_dict(data)

    def _render_env_dict(self, data):
        node = dict()
        for k, v in data.items():
            if isinstance(v, str):
                node[k] = v.format(**self.env)
            elif isinstance(v, dict):
                node[k] = self._render_env_dict(v)
            elif isinstance(v, list):
                node[k] = self._render_env_list(v)
            else:
                node[k] = v

        return node

    def _render_env_list(self, data):
        node = list()
        for item in data:
            if isinstance(item, str):
                node.append(item.format(**self.env))
            elif isinstance(item, dict):
                node.append(self._render_env_dict(item))
            elif isinstance(item, list):
                node.append(self._render_env_list(item))
            else:
                node.append(item)

        return node

    def __repr__(self):
        return json.dumps(self.env)


class RequestBuilder():

    def build(self, info):
        self.clear()
        self.headers = info.headers or Arguments()
        self.content_type = info.content_type or self.guess_content_type()

        data = dict()
        data['url'] = info.url
        data['method'] = info.method
        data['headers'] = dict(info.headers or dict())
        data['params'] = dict(info.query or dict())

        if isinstance(info.body, str):
            data['data'] = info.body
        elif self.content_type == 'json':
            data['json'] = info.body
        else:
            data['data'] = info.body

        self.prepared = requests.Request(**data).prepare()

    def send(self):
        if not self.prepared:
            raise ValueError('Request is not prepared.')
        return requests.Session().send(self.prepared)

    def clear(self):
        self.headers = None
        self.content_type = None
        self.prepared = None

    def guess_content_type(self):
        content_type = self.headers.get('Content-Type')

        if content_type == 'application/x-www-form-urlencoded':
            return 'urlencode'
        elif content_type == 'application/json':
            return 'json'
        else:
            return 'json'

    def raw_print(self):
        if not self.prepared:
            raise ValueError('Request is not prepared.')
        method = self.prepared.method
        url = self.prepared.url
        headers = '\n'.join(
            f'{k}: {v}' for k, v in self.prepared.headers.items())
        body = self.prepared.body
        print('-----------START-----------')
        print(f'{method} {url}\n{headers}\n\n{body}')
        print('-----------ENDED-----------')


class Checker():

    _expression = re.compile(r'(\$[a-z]+)( *: *)([^;]*)')

    def __init__(self, info, tc, start=None):
        self.tc = tc
        self._operator = {
            '$lt': lambda x, y: self.tc.assertLess(x, y),
            '$le': lambda x, y: self.tc.assertLessEqual(x, y),
            '$gt': lambda x, y: self.tc.assertGreater(x, y),
            '$ge': lambda x, y: self.tc.assertGreaterEqual(x, y),
            '$eq': lambda x, y: self.tc.assertEqual(x, y),
            '$ne': lambda x, y: self.tc.assertNotEqual(x, y),
            '$in': lambda x, y: self.tc.assertIn(x, y),
            '$is': lambda x, y: self.tc.assertIs(x, y),
            '$isnot': lambda x, y: self.tc.assertIsNot(x, y),
        }
        if not start:
            start = []
        elif isinstance(start, str):
            start = [start]

        self.info = info
        self.check_map = dict()
        self._parse(start, info)

    def _parse(self, cur, data):
        if isinstance(data, list):
            gen = enumerate(data)
        elif isinstance(data, dict):
            gen = data.items()
        else:
            raise TypeError(f'Unknown type "{type(data)}" of data.')

        for k, v in gen:
            path = cur + [str(k)]
            if isinstance(v, (str, int, float)):
                self.check_map['.'.join(path)] = v
            elif isinstance(v, (dict, list)):
                self._parse(path, v)
            else:
                raise TypeError(f'Unknown type "{type(v)}" of key "{k}"')

    def check(self, resp):
        for k, checker in self.check_map.items():
            value = self.get_value(k, resp)
            self.check_item(checker, value)

    def get_value(self, path, resp):
        value = resp
        for p in path.split('.'):
            if p in value:
                value = value[p]
            elif p.isdigit():
                i = int(p)
                if not isinstance(value, list):
                    return 1
                elif len(value) <= i:
                    return 2
                else:
                    value = value[p]
            else:
                return None
        return value

    def check_item(self, exp, checkee):
        matcher = self._expression.match(exp)
        if not matcher:
            raise ValueError(f'Unkown expression {exp}')

        operator, _, answer = matcher.groups()
        answer = eval(answer, {'__buildins__': None})

        return self.test(operator, checkee, answer)

    def test(self, operator, a, b):
        if operator not in self._operator:
            raise KeyError(f'Unknown operator "{operator}"')
        return self._operator[operator](a, b)
