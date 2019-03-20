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
from tornado.web import Finish, RequestHandler, HTTPError
from tornado.log import app_log, gen_log

from tarpit.config import CONFIG as O_O, get_status_message
from tarpit.entity import Arguments, ParseJSONError
from tarpit.utils import dump_in, dump_out, dump_error, json_encoder
from tarpit.task import TaskError, SERVICES
from tarpit.dao import MongoFactory

ROUTES = []


def check_params(func):
    """Decorator to create a parameters checker."""
    parameters = inspect.signature(func).parameters

    for name, value in parameters.items():
        if value.kind == value.VAR_KEYWORD:
            continue
        if value.kind == value.VAR_POSITIONAL:
            continue

        if value.annotation == value.empty:
            raise ValueError(f'Annotation of key <"{name}"> is not exists.')

    def inner(**kwargs):
        for name, value in parameters.items():
            if value.kind == value.VAR_KEYWORD:
                continue
            if value.kind == value.VAR_POSITIONAL:
                continue

            if kwargs.get(name) is None:
                if value.default != value.empty:
                    kwargs[name] = value.default
                else:
                    raise MissingArgumentError(name)

            if kwargs[name] is not None and not isinstance(
                    kwargs[name], value.annotation):
                try:
                    kwargs[name] = value.annotation(kwargs[name])
                except:
                    raise ArgumentTypeError(name, value.annotation)

        return kwargs

    return inner


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


def recursive_import(submodule_location, submodule_name=''):
    dirname = submodule_name and (submodule_name + '.')
    module_dict = dict()
    for m in pkgutil.iter_modules(submodule_location):
        if m.ispkg:
            location = f'{submodule_location[0]}/{m.name}'
            recursive_import([location], submodule_name=f'{dirname}{m.name}')
        else:
            module_dict[m.name] = importlib.import_module(f'{dirname}{m.name}')


class Auth:

    def __init__(self, optional=False, **options):
        self.options = options
        self.optional = optional

    def __new__(cls, func=None, **options):
        instance = super(Auth, cls).__new__(cls)
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


class MissingArgumentError(HTTPError):
    """Missing Argument Error."""

    def __init__(self, arg_name):
        super(MissingArgumentError, self).__init__(
            400, f'Missing argument "{arg_name}"')
        self.arg_name = arg_name


class TokenExpiredError(HTTPError):
    """Token Expired Error."""

    def __init__(self):
        super(TokenExpiredError, self).__init__(401, 'Token Expired')


class ArgumentTypeError(HTTPError):
    """Argument Type Error."""

    def __init__(self, arg_name, type_name):
        super(ArgumentTypeError, self).__init__(
            400, f'Argument "{arg_name}" should be {type_name}')


class InternalServerError(HTTPError):
    """Task Error."""

    def __init__(self, task_name, error_msg):
        super(InternalServerError, self).__init__(
            500, f'Error occured when excute task "{task_name}".\n{error_msg}')


class AuthenticationError(HTTPError):
    """Authentication Error."""

    def __init__(self, msg):
        super(AuthenticationError, self).__init__(401, msg)


class AuthorizationError(HTTPError):
    """Authorization Error."""

    def __init__(self, arg_name):
        super(AuthorizationError, self).__init__(
            401, f'User\'s "{arg_name}" not satisfied.')


class Mission:

    def __init__(self, func):
        if not callable(func):
            self.func = self.none_func
            self.func_name = 'none_func'
            raise TypeError(f'Need callable Object, not {type(func)}')
        self.func_name = func.__name__
        self.func = func

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

        res = self.func(*args, **kwargs)
        if isinstance(res, TaskError):
            raise InternalServerError(self.func_name, res.get_json_object())

        return res


class ServiceFactory(dict):

    def __init__(self, params=None):
        if isinstance(params, dict):
            super().__init__(params)
        elif not params:
            super().__init__(dict())
        else:
            raise TypeError(
                f"Arguments data should be a 'dict' not {type(params)}.")

    def __getattr__(self, name):
        attr = self.get(name)
        if isinstance(attr, dict):
            return self.__class__(attr)
        else:
            return Mission(attr)

    def __setattr__(self, name, value):
        raise PermissionError('Can not set attribute to <class Arguments>.')


class BaseController(RequestHandler):
    """Custom handler for other views module."""

    def __init__(self, application, request, **kwargs):
        super(BaseController, self).__init__(application, request, **kwargs)
        self.params = Arguments()
        self.token_args = Arguments()
        self.mg = MongoFactory()
        self.s = ServiceFactory(SERVICES)

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
            app_log.error(
                "Uncaught exception %s\n%r",
                self._request_summary(),
                self.request,
                exc_info=(typ, value, tb))

    async def options(self, *_args, **_kwargs):
        self.success()

    def prepare(self):
        params = dict(
            device=self.get_argument('device', 'web'),
            lang=self.get_argument('lang', 'cn').lower(),
            remote_ip=self.request.remote_ip,
            request_time=time.time())
        self.params = Arguments(params)

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE')
        self.set_header('Access-Control-Allow-Headers',
                        'Authorization,Content-Type,Thor-Token')

    def get_token(self):
        header_name = O_O.server.token_header or 'Thor-Token'
        token = self.request.headers.get(header_name)
        try:
            return jwt.decode(token, O_O.server.token_secret)
        except jwt.DecodeError:
            return None

    def set_token(self, token_params: dict = None, expired: int = 3600):
        token_params = token_params or dict()
        token = jwt.encode(
            dict(token_params, timestamp=int(time.time()) + expired),
            O_O.server.token_secret)
        self.set_header(O_O.server.token_header or 'Thor-Token', token)

    def parse_form_arguments(self, checker=None):
        """Parse FORM argument like `get_argument`."""
        if O_O.debug:
            dump_in(f'Input: {self.request.method} {self.request.path}',
                    self.request.body.decode()[:500])

        args = {
            k: v[0].decode() for k, v in self.request.arguments.items() if v[0]
        }

        if checker:
            args = checker(**args)

        return Arguments(args)

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

        if checker:
            args = checker(**args)

        return Arguments(args)

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
        self.finish_with_json(
            dict(status=status, msg=msg, data=data, **_kwargs))

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
