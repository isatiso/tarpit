# coding:utf-8
"""Views Module."""
import inspect
import time

from tarpit.config import CONFIG as O_O
from tarpit.web import BaseController, route, check_params, Auth
from tarpit.utils.totp import get_totp_token


@route(r'/')
class Account(BaseController):
    """account"""

    @Auth
    async def get(self, *_args, **_kw):

        result = await self.s.user.get_account_info(
            user_id=self.token_args.user_id)

        self.success(result)

    @Auth
    async def put(self, *_args, **_kw):

        @check_params
        def checker(
                name: str = None,
                phone: str = None,
                avatar: str = None,
        ):
            pass

        args = self.parse_json_arguments(checker)

        result = await self.s.user.modify_account_info(
            user_id=self.token_args.user_id,
            name=args.name,
            phone=args.phone,
            avatar=args.avatar,
        )

        self.success(result)


@route(r'/modify_password')
class AccountModifyPassword(BaseController):
    """acccount modify password"""

    @Auth
    async def post(self, *_args, **_kw):

        @check_params
        def checker(user_id: int, oldpass: str, newpass: str):
            pass

        args = self.parse_json_arguments(checker)

        user_info = await self.s.user.check_password_by_id(
            user_id=self.token_args.user_id, password=args.oldpass)

        if not user_info:
            self.fail(401)

        result = await self.s.set_password(
            user_id=args.user_id,
            password=args.password,
        )

        self.success(result)


@route(r'/address')
class AccountAddress(BaseController):
    """account address"""

    @Auth
    async def get(self, *_args, **_kw):

        @check_params
        def checker(address_id: int):
            pass

        args = self.parse_form_arguments(checker)

        result = await self.s.address.get_address_info(
            address_id=args.address_id)

        self.success(result)

    @Auth
    async def post(self, *_args, **_kw):

        @check_params
        def checker(recipient: str, phone: str, address: str):
            pass

        args = self.parse_json_arguments(checker)

        await self.s.address.create_address(
            user_id=self.token_args.user_id,
            recipient=args.recipient,
            phone=args.phone,
            address=args.address)

        self.success()

    @Auth
    async def put(self, *_args, **_kw):

        @check_params
        def checker(
                address_id: int,
                recipient: str = None,
                phone: str = None,
                address: str = None,
        ):
            pass

        args = self.parse_json_arguments(checker)

        await self.s.address.modify_address_info(
            address_id=args.address_id,
            recipient=args.recipient,
            phone=args.phone,
            address=args.address)

        self.success()

    @Auth
    async def delete(self, *_args, **_kw):

        @check_params
        def checker(address_id: int):
            pass

        args = self.parse_form_arguments(checker)

        await self.s.address.delete_address(address_id=args.address_id)

        self.success()


@route(r'/address/list')
class AccountAddressList(BaseController):
    """account list"""

    @Auth
    async def get(self, *_args, **_kw):

        result = await self.s.address.get_address_list(
            user_id=self.token_args.user_id)

        self.success(dict(infos=result))


@route(r'/signin')
class SignIn(BaseController):
    """sign in"""

    async def post(self, *_args, **_kw):

        @check_params
        def checker(username: str, password: str):
            pass

        args = self.parse_form_arguments(checker)

        user_info = await self.s.user.check_password(
            username=args.username, password=args.password)

        if not user_info:
            self.fail(404)
        if user_info.role > 0:
            self.fail(401)

        self.set_token(user_info)
        self.set_header('Access-Control-Expose-Headers',
                        O_O.server.token_header)

        self.success(user_info)
