# coding:utf-8
import time
import requests

import gevent

from tarpit.dao import dict_of
from tarpit.task import service
from tarpit.utils.generate import encode_passwd


@service(mappers=['user', 'user_wallet'])
def create_account(self, name, phone, password, role, avatar):
    mapper = self.get_mapper()

    password = encode_passwd(password)
    user = mapper.insert_user(name, phone, password, role, avatar)
    mapper.insert_wallet(user.user_id)

    self.commit()

    return dict(user_id=user.user_id)


@service(mappers=['user'])
def delete_account(self, user_id):

    mapper = self.get_mapper()
    user = mapper.update_user_deleted(user_id, 1)
    self.commit()

    return dict(user_id=user.user_id)


@service(mappers=['user'])
def get_account_info(self, user_id):
    mapper = self.get_mapper()
    user_info, balance = mapper.query_user_by_id(user_id)
    option = ['user_id', 'name', 'phone', 'avatar', 'role', 'banned', 'deleted']
    return dict(dict_of(user_info, *option), balance=balance)
