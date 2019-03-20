# coding:utf-8
"""Views Module."""
import inspect
import time

from tarpit.config import CONFIG as O_O
from tarpit.web import BaseController, route, check_params, Auth, AuthorizationError
from tarpit.task import SERVICES


@route(r'/')
class Index(BaseController):
    """Test index request handler."""

    async def get(self, *_args, **_kwargs):
        """Get method of IndexHandler."""
        self.mg.image.insert_image()
        self.finish(b'<h1>Dejavu!</h1>')


@route(r'*.php')
class PHPScan(BaseController):
    """Test index request handler."""

    async def get(self, *_, **__):
        """return f word."""

        self.finish(b'fuck you')
