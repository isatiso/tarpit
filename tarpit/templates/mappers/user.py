from sqlalchemy.orm import Query
from sqlalchemy import or_

from database.sqlalchemy_models import User
from tarpit.dao import BaseMapper


class UserMapper(BaseMapper):
    """User Query Factory."""

    __alias__ = 'user'

    def insert_user(self, name, phone, password, role, avatar, **kwargs):
        user = User(
            name=name, phone=phone, password=password, role=role, avatar=None)
        self.session.add(user)
        return user

    def update_user_name(self, user_id, name, **kwargs):
        query = self.session.query(User).filter(User.user_id == user_id)
        return query.update(dict(name=name))

    def update_user_phone(self, user_id, phone, **kwargs):
        query = self.session.query(User).filter(User.user_id == user_id)
        return query.update(dict(phone=phone))

    def update_user_avatar(self, user_id, avatar, **kwargs):
        query = self.session.query(User).filter(User.user_id == user_id)
        return query.update(dict(avatar=avatar))

    def update_user_password(self, user_id, password, **kwargs):
        query = self.session.query(User).filter(User.user_id == user_id)
        return query.update(dict(password=password))

    def query_user_by_id(self, user_id, **kwargs):
        query = self.session.query(User)
        query = query.filter(User.user_id == user_id)
        return query.first()