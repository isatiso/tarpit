# coding:utf-8
"""Module of celery task queue manager."""

import os
import pkgutil
import importlib
import asyncio
import traceback
from functools import wraps

from celery import Celery
from celery.app import trace
from kombu.serialization import register
from sqlalchemy import exc as sqlexc
import pymysql

from .err import ServiceError
from .config import CONFIG as O_O, _ENV as env
from .dao import transaction
from .utils import json_encoder, dump_in, dump_out, dump_error, tarpit_dumps, tarpit_loads

register(
    'tarpit_json',
    tarpit_dumps,
    tarpit_loads,
    content_type='application/json',
    content_encoding='utf-8')

trace.LOG_SUCCESS = '\033[0;33mTask [%(id)s] succeeded in %(runtime)1.6ss %(name)s\033[0m'


class CeleryConfig():

    _instance = None
    _app = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(CeleryConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.queue_list = {
            'user_service': dict(concurrency=3, module='services.user_service')
        }

        self._app = Celery(
            'tasks',
            backend=O_O.celery.backend,
            broker=O_O.celery.broker,
        )

        self._app.conf.update(
            task_serializer='tarpit_json',
            result_serializer='tarpit_json',
            result_expires=180,
            broker_connection_timeout=10,
            broker_pool_limit=10,
            broker_heartbeat=40,
            broker_heartbeat_checkrate=2,
            enable_utc=True,
            timezone='Asia/Hong_Kong',
            task_default_queue='default',
            task_default_exchange='tasks',
            task_default_exchange_type='topic',
            task_default_routing_key='task.default',
            worker_max_memory_per_child=2048,
            worker_log_format=
            '[%(asctime)19.19s %(levelname)1.1s/%(processName)s] %(message)s',
            task_routes={
                f'services.{q}.*': {
                    'queue': f'{env}:{q}'
                } for q in self.queue_list
            },
        )

    @property
    def app(self):
        return self._app


CELERY_CMD = os.getenv('celery_cmd', default='celery')

SERVICES = dict()


class TaskError(Exception):
    """An exception that will turn into an DAO error response.

    :arg int status: Custom DAO status code.
    :arg str message: Message to be written to the log for this error
        (will not be shown to the user unless the `Application` is in debug
        mode).  May contain ``%s``-style placeholders, which will be filled
        in with remaining positional parameters.
    """

    def __init__(self, error):
        try:
            raise error
        except sqlexc.IntegrityError as err:
            self.set_status(1, str(err.orig), err.__class__.__name__)
        except sqlexc.ProgrammingError as err:
            self.set_status(2, str(err.orig), err.__class__.__name__)
        except sqlexc.ResourceClosedError as err:
            self.set_status(3, str(error), err.__class__.__name__)
        except sqlexc.OperationalError as err:
            self.set_status(4, str(err.orig), err.__class__.__name__)
        except UnicodeEncodeError as err:
            self.set_status(5, str(error), err.__class__.__name__)
        except sqlexc.DataError as err:
            self.set_status(6, str(err.orig), err.__class__.__name__)
        except sqlexc.InternalError as err:
            self.set_status(7, str(err.orig), err.__class__.__name__)
        except Exception as err:
            self.set_status(255, str(err), err.__class__.__name__)

    def set_status(self, status, message, error_type):
        self.status = status
        self.message = message
        self.error_type = error_type

    def get_json_object(self):
        return dict(
            status=self.status,
            message=self.message,
            error_type=self.error_type)


def catch_error(function):
    """Wrap a handle shell to a query function."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        """Function that wrapped."""
        try:
            return function(*args, **kwargs)
        except ServiceError as e:
            raise e
        except Exception as e:
            raise TaskError(e)

    return wrapper


def assemble_celery_cmd(queue):
    cc = CeleryConfig()
    concurrency = cc.queue_list[queue]['concurrency']
    return (f'{CELERY_CMD}', 'worker', '-A', 'worker.app', '-c',
            f'{concurrency}', '-P', 'gevent', '-Q', f'{env}:{queue}', '-n',
            f'{env}:{queue}@%h', f'--loglevel=info')


class Service:

    def __init__(self, mappers=None, celery_params=None):
        self.mappers = mappers or []
        self.celery_params = celery_params or dict()
        self.cur = SERVICES

    def __call__(self, func):

        func = transaction(func, self.mappers)
        func = catch_error(func)

        cc = CeleryConfig()

        if self.celery_params:
            func = cc.app.task(**self.celery_params)(func)
        else:
            func = cc.app.task(func)

        filename = traceback.extract_stack(limit=2)[0].filename
        if '/services' in filename:
            filedir = os.path.dirname(filename).split('/services')[-1]

            modules = filedir.strip('/').split('/')
            filename = os.path.basename(filename)
            filename = os.path.splitext(filename)[0]
            modules.append(filename)

            cur = SERVICES

            for m in modules:
                if not m:
                    continue
                if m not in cur:
                    cur[m] = dict()
                cur = cur[m]
            cur[func.__name__] = func

        return func


def service(mappers=None, celery_params=None, need_transaction=True):
    """Wrapper of 'app.task'."""

    def decorator(func):
        if need_transaction:
            func = transaction(func, mappers or [])

        func = catch_error(func)

        cc = CeleryConfig()
        if celery_params and isinstance(celery_params, dict):
            func = cc.app.task(**celery_params)(func)
        else:
            func = cc.app.task(func)

        filename = traceback.extract_stack(limit=2)[0].filename
        if '/services' in filename:
            filedir = os.path.dirname(filename).split('/services')[-1]

            modules = filedir.strip('/').split('/')
            filename = os.path.basename(filename)
            filename = os.path.splitext(filename)[0]
            modules.append(filename)

            cur = SERVICES

            for m in modules:
                if not m:
                    continue
                if m not in cur:
                    cur[m] = dict()
                cur = cur[m]
            cur[func.__name__] = func

        return func

    return decorator
