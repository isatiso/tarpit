# coding:utf-8
"""Views Module."""
import inspect
import time

from tarpit.config import CONFIG as O_O
from tarpit.web import BaseController, route, auth
from tarpit.utils.totp import get_totp_token
from tarpit.checker import P, M


@route(r'/')
class Account(BaseController):
    """account"""

    @auth
    async def get(self, *_args, **_kw):

        result = await self.miss.user.get_account_info(
            user_id=self.token_args.user_id)

        self.success(result)

    @auth
    async def put(self, *_args, **_kw):

        args = self.check_params({
            P('name') >> str,
            P('phone') >> str,
            P('avatar') >> str,
        })

        result = await self.miss.user.modify_account_info(
            user_id=self.token_args.user_id,
            name=args.name,
            phone=args.phone,
            avatar=args.avatar,
        )

        self.success(result)


@route(r'/modify_password')
class AccountModifyPassword(BaseController):
    """acccount modify password"""

    @auth
    async def post(self, *_args, **_kw):

        args = self.check_params({
            M('user_id') >> int,
            M('oldpass') >> str,
            M('newpass') >> str,
        })

        user_info = await self.miss.user.check_password_by_id(
            user_id=self.token_args.user_id, password=args.oldpass)

        if not user_info:
            self.fail(401)

        result = await self.miss.set_password(
            user_id=args.user_id,
            password=args.password,
        )

        self.success(result)


@route(r'/address')
class AccountAddress(BaseController):
    """account address"""

    @auth
    async def get(self, *_args, **_kw):

        args = self.check_params({
            M('address_id') >> int,
        })

        result = await self.miss.address.get_address_info(
            address_id=args.address_id)

        self.success(result)

    @auth
    async def post(self, *_args, **_kw):

        args = self.check_params({
            M('recipient') >> str,
            M('phone') >> str,
            M('address') >> str,
        })

        await self.miss.address.create_address(
            user_id=self.token_args.user_id,
            recipient=args.recipient,
            phone=args.phone,
            address=args.address)

        self.success()

    @auth
    async def put(self, *_args, **_kw):

        args = self.check_params({
            M('address_id') >> int,
            P('recipient') >> str,
            P('phone') >> str,
            P('address') >> str,
        })

        await self.miss.address.modify_address_info(
            address_id=args.address_id,
            recipient=args.recipient,
            phone=args.phone,
            address=args.address)

        self.success()

    @auth
    async def delete(self, *_args, **_kw):

        args = self.check_params({
            M('address_id') >> int,
        })

        await self.miss.address.delete_address(address_id=args.address_id)

        self.success()


@route(r'/address/list')
class AccountAddressList(BaseController):
    """account list"""

    @auth
    async def get(self, *_args, **_kw):

        result = await self.miss.address.get_address_list(
            user_id=self.token_args.user_id)

        self.success(dict(infos=result))


@route(r'/signin')
class SignIn(BaseController):
    """sign in"""

    async def post(self, *_args, **_kw):

        args = self.check_params({
            M('username') >> str,
            M('password') >> str,
        })

        user_info = await self.miss.user.check_password(
            username=args.username, password=args.password)

        if not user_info:
            self.fail(404)
        if user_info.role > 0:
            self.fail(401)

        self.set_token(user_info)
        self.set_header('Access-Control-Expose-Headers',
                        O_O.server.token_header)

        self.success(user_info)
