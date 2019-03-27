# coding:utf-8
"""Views Module."""
import inspect
import time

from tarpit.config import CONFIG as O_O
from tarpit.toolkit import P, route, BaseController


@route(r'/')
class Index(BaseController):
    """Test index request handler."""

    async def get(self, *_args, **_kwargs):
        """Get method of IndexHandler."""

        args = self.check_params({
            P('a') >> str,
            P('b') >> int,
        })

        self.finish(f'<h1>Dejavu! {args.a} {args.b}</h1>'.encode())


@route(r'*.php')
class PHPScan(BaseController):
    """Test index request handler."""

    async def get(self, *_, **__):
        """return f word."""

        self.finish(b'fuck you')
