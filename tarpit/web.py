# coding:utf-8
"""Base module for other views' modules."""
import json
import re
import time
import traceback
import os
import pkgutil
import importlib
import asyncio
from functools import wraps
from collections import abc
from urllib import parse
import inspect

import jwt
from tornado import gen, httpclient
from tornado.web import Finish, RequestHandler
from tornado.log import app_log, gen_log

from .err import *
from .config import CONFIG as O_O, get_status_message
from .utils import Arguments, dump_in, dump_out, dump_error, json_encoder
from .checker import M
from .task import TaskError, SERVICES
from .dao import MongoFactory

ROUTES = []


def route(*path_list: str):
    """Decorator to bind path to a hander."""

    def wrapper(handler: RequestHandler):
        if not issubclass(handler, RequestHandler):
            raise PermissionError('Can\'t routing a nonhandler class.')

        filename = traceback.extract_stack(limit=2)[0].filename
        if '/controllers' in filename:
            filedir = os.path.dirname(filename).split('/controllers')[-1]
            filedir = filedir.strip('/')
            filename = os.path.basename(filename)
            filename = os.path.splitext(filename)[0]
            filename = '' if filename == 'index' else filename
            for path in path_list:
                realpath = path.strip('/')
                realpath = '/' + f'{filedir}/{filename}/{realpath}'.strip('/')
                ROUTES.append((realpath, handler))
        return handler

    return wrapper


class auth:

    def __init__(self, optional=False, **options):
        self.options = options
        self.optional = optional

    def __new__(cls, func=None, **options):
        instance = super(auth, cls).__new__(cls)
        instance.__init__(**options)
        if func:
            return instance(func)
        else:
            return instance

    def __call__(self, func):
        """Decorator to check authorization of user."""

        def process(ctlr):
            ctlr.set_header('Access-Control-Allow-Origin', '*')
            token_params = Arguments(ctlr.get_token())
            now = int(time.time())
            if not self.optional:
                if not token_params:
                    raise AuthenticationError('Token is empty.')
                if 'timestamp' not in token_params:
                    raise AuthenticationError('No timestamp info in token.')
                if token_params.timestamp < now:
                    raise TokenExpiredError()

                for key in self.options:
                    if isinstance(self.options[key], abc.Iterable):
                        if token_params.get(key) not in self.options[key]:
                            raise AuthorizationError(key)
                    else:
                        if token_params.get(key) != self.options[key]:
                            raise AuthorizationError(key)

            ctlr.token_args = Arguments(token_params)

        @wraps(func)
        async def async_wrapper(ctlr, **kwargs):
            process(ctlr)
            await func(ctlr, **kwargs)

        @wraps(func)
        def wrapper(ctlr, **kwargs):
            process(ctlr)
            func(ctlr, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper


class Mission:

    def __init__(self, func, controller):
        if not callable(func):
            self.func = self.none_func
            self.func_name = 'none_func'
            raise TypeError(f'Need callable Object, not {type(func)}')
        self.func_name = func.__name__
        self.func = func
        self.controller = controller

    @staticmethod
    def none_func(*args, **kwargs):
        return 'Uncallable function.'

    async def __call__(self, *args, **kwargs):

        if not O_O.worker.mode:
            return self.run(*args, **kwargs)

        async_task = self.func.apply_async(args=args, kwargs=kwargs)

        while not async_task.ready():
            asyncio.sleep(0)

        if async_task.failed():
            dump_error(f'Task Failed: {self.func_name}[{async_task.task_id}]',
                       f'    {str(async_task.result)}')
            raise RuntimeError(str(async_task.result))
        else:
            result = async_task.result

        if isinstance(result, dict) and result.get('error_type'):
            raise RuntimeError(str(async_task.result))
        else:
            return result

    def run(self, *args, **kwargs):

        try:
            res = self.func(*args, **kwargs)
        except ServiceError as e:
            self.controller.fail(e.code + 5000)
        except TaskError as e:
            raise InternalServerError(self.func_name, e.get_json_object())

        return res


class MissionFactory(dict):

    controller = None

    def __init__(self, params=None, controller=None):
        self.controller = controller
        if isinstance(params, dict):
            super().__init__(params)
        elif not params:
            super().__init__(dict())
        else:
            raise TypeError(
                f"Arguments data should be a 'dict' not {type(params)}.")

    def __getattr__(self, name):
        if name in self:
            attr = self.get(name)
            if isinstance(attr, dict):
                return self.__class__(attr, self.controller)
            else:
                return Mission(attr, self.controller)
        else:
            return self.__getattribute__(name)


class BaseController(RequestHandler):
    """Custom handler for other views module."""

    def __init__(self, application, request, **kwargs):
        super(BaseController, self).__init__(application, request, **kwargs)
        self.params = Arguments()
        self.token_args = Arguments()
        self.mg = MongoFactory()
        self.miss = MissionFactory(SERVICES, self)

    def _request_summary(self):
        s = ' '
        return f'{self.request.method.rjust(7, s)} {self.request.remote_ip.rjust(15, s)}  {self.request.path} '

    def log_exception(self, typ, value, tb):
        """Override to customize logging of uncaught exceptions.

        By default logs instances of `HTTPError` as warnings without
        stack traces (on the ``tornado.general`` logger), and all
        other exceptions as errors with stack traces (on the
        ``tornado.application`` logger).

        .. versionadded:: 3.1
        """
        if isinstance(value, HTTPError):
            if value.log_message:
                # format = "%d %s: " + value.log_message
                # args = ([value.status_code,
                #          self._request_summary()] + list(value.args))
                gen_log.warning('\033[0;31m' + value.log_message + '\033[0m')
        else:
            app_log.error("Uncaught exception %s\n%r",
                          self._request_summary(),
                          self.request,
                          exc_info=(typ, value, tb))

    async def options(self, *_args, **_kwargs):
        self.success()

    def prepare(self):
        params = dict(device=self.get_argument('device', 'web'),
                      lang=self.get_argument('lang', 'cn').lower(),
                      remote_ip=self.request.remote_ip,
                      request_time=time.time())
        self.params = Arguments(params)

    def set_default_headers(self):
        origin = O_O.server.access_control_allow_origin or '*'
        methods = O_O.server.access_control_allow_methods or 'GET,POST,PUT,DELETE'
        headers = O_O.server.access_control_allow_headers or 'Authorization,Content-Type,Token'
        self.set_header('Access-Control-Allow-Origin', origin)
        self.set_header('Access-Control-Allow-Methods', methods)
        self.set_header('Access-Control-Allow-Headers', headers)

    def get_token(self):
        header_name = O_O.server.token_header or 'Token'
        token = self.request.headers.get(header_name)
        try:
            return jwt.decode(token, O_O.server.token_secret)
        except jwt.DecodeError:
            return None

    def set_token(self, token_params: dict = None, expired: int = 3600):
        if not token_params:
            token_params = dict()
            expired = 0
        token = jwt.encode(
            dict(token_params, timestamp=int(time.time()) + expired),
            O_O.server.token_secret)
        token_name = O_O.server.token_header or 'Token'
        self.set_header('Access-Control-Expose-Headers', token_name)
        self.set_header(token_name, token)

    def _check_params(self, args, checker):
        for param_type in checker:
            # 设置默认值
            key = param_type.name
            if args.get(key) is None:
                if param_type.optional:
                    args[key] = param_type.default
                else:
                    raise MissingArgumentError(param_type.name)

            if param_type.type in (int, float, str, bool):
                if args[key] is None:
                    continue
                elif not isinstance(args[key], param_type.type):
                    try:
                        args[key] = param_type.type(args[key])
                    except:
                        raise ArgumentTypeError(key, param_type.type)
            elif param_type.type == list:
                if not isinstance(args[key], list):
                    raise ArgumentTypeError(key, list)
                if isinstance(param_type.subparam, type):
                    for i, obj in enumerate(args[key]):
                        if not isinstance(obj, param_type.subparam):
                            try:
                                args[key][i] = param_type.subparam(obj)
                            except:
                                raise ArgumentTypeError(f'{key}.{i}', param_type.subparam)
                else:
                    for obj in args[key]:
                        self._check_params(obj, param_type.subparam)
            elif param_type.type == set:
                if not isinstance(args[key], dict):
                    raise ArgumentTypeError(key, dict)
                self._check_params(args[key], param_type.subparam)
            else:
                raise TypeError(f'Unkown type {type(checker[key])}')

    def check_params(self, checker=None):
        if self.request.method in ('GET', 'DELETE', 'HEAD'):
            args = self.parse_form_arguments(checker)
        else:
            args = self.parse_json_arguments(checker)

        self._check_params(args, checker)

        return Arguments(args)

    def parse_form_arguments(self, checker=None):
        """Parse FORM argument like `get_argument`."""
        if O_O.debug:
            dump_in(f'Input: {self.request.method} {self.request.path}',
                    self.request.body.decode()[:500])

        args = {
            k: v[0].decode() for k, v in self.request.arguments.items() if v[0]
        }

        return args

    def parse_json_arguments(self, checker=None):
        """Parse JSON argument like `get_argument`."""
        if O_O.debug:
            dump_in(f'Input: {self.request.method} {self.request.path}',
                    self.request.body.decode()[:500])

        try:
            args = json.loads(self.request.body.decode('utf-8'))
        except json.JSONDecodeError as exception:
            dump_error(self.request.body.decode())
            raise ParseJSONError(exception.doc)

        if not isinstance(args, dict):
            dump_error(self.request.body.decode())
            raise ParseJSONError('Request body should be a dictonary.')

        return args

    def finish_with_json(self, data):
        """Turn data to JSON format before finish."""
        self.set_header('Content-Type', 'application/json')

        if O_O.debug:
            if self.request.method == 'POST':
                info_list = [
                    f'\033[0;33mOutput: {self.request.method} {self.request.path}'
                ]
                if self.request.query:
                    query_list = [
                        f'\033[0;33m{i[0]:15s} {i[1]}'
                        for i in parse.parse_qsl(self.request.query)
                    ]
                    info_list.append('\n' + '\n'.join(query_list))
                if self.request.body:
                    try:
                        info_list.append('\n\033[0;33m' +
                                         self.request.body.decode())
                    except UnicodeDecodeError:
                        pass
                if data:
                    info_list.append('\n\033[0;33m' + json.dumps(data))
                dump_out(*info_list)

        raise Finish(json.dumps(data).encode())

    def fail(self, status, data=None, polyfill=None, **_kwargs):
        """assemble and return error data."""
        msg = get_status_message(status)
        self.finish_with_json(dict(status=status, msg=msg, data=data,
                                   **_kwargs))

    def success(self, data=None, msg='Successfully.', **_kwargs):
        """assemble and return error data."""
        self.finish_with_json(dict(status=0, msg=msg, data=data))

    async def fetch(self, api, method='GET', body=None, headers=None,
                    **_kwargs):
        """Fetch Info from backend."""
        body = body or dict()

        _headers = dict(host=self.request.host)
        if headers:
            _headers.update(headers)

        if '://' not in api:
            api = f'http://{O_O.server.back_ip}{api}'

        back_info = await httpclient.AsyncHTTPClient().fetch(
            api,
            method=method,
            headers=_headers,
            body=json.dumps(body),
            raise_error=False,
            allow_nonstandard_methods=True)

        res_body = back_info.body and back_info.body.decode() or None

        if back_info.code >= 400:
            return Arguments(
                dict(http_code=back_info.code, res_body=res_body, api=api))

        try:
            return Arguments(json.loads(res_body))
        except json.JSONDecodeError:
            raise ParseJSONError(res_body)
