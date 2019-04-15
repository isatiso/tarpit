import os
import sys
import shutil
import pkgutil
import importlib
from tornado import ioloop
from tornado.web import Application
from tornado.log import enable_pretty_logging

from .web import ROUTES
from .config import CONFIG as O_O


def recursive_import(submodule_location, submodule_name=''):
    dirname = submodule_name and (submodule_name + '.')
    module_dict = dict()
    for m in pkgutil.iter_modules(submodule_location):
        if m.ispkg:
            location = f'{submodule_location[0]}{os.sep}{m.name}'
            recursive_import([location], submodule_name=f'{dirname}{m.name}')
        else:
            module_dict[m.name] = importlib.import_module(f'{dirname}{m.name}')


def set_dependence(module):
    recursive_import(module.__spec__.submodule_search_locations,
                     module.__name__)


def generate(dst):
    src = os.path.join(os.path.dirname(__file__), 'templates')
    shutil.copytree(src, dst)


def serve():

    sys.path.append(os.getcwd())
    mappers = __import__('mappers')
    services = __import__('services')
    controllers = __import__('controllers')
    storage = __import__('storage')
    set_dependence(storage)
    set_dependence(mappers)
    set_dependence(services)
    set_dependence(controllers)

    enable_pretty_logging()

    for r in ROUTES:
        print(f'{r[0]:30s} {r[1]}')

    app = Application(handlers=ROUTES, **O_O.application)
    app.listen(O_O.server.port, **O_O.httpserver)

    O_O.show()
    print('\nstart listen...')
    ioloop.IOLoop.instance().start()