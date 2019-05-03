# coding:utf-8
"""Lazor Database Module."""
import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import func, text, inspect, Column
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base():

    def as_dict(self, *options, **alias):
        if self is None:
            return dict()

        res = dict()
        for key in options:
            alias[key] = None

        for col in inspect(self).mapper.column_attrs:
            key = col.key
            if not alias or key in alias:
                if isinstance(alias.get(key), str):
                    real_key = alias[key]
                else:
                    real_key = key
                if isinstance(self.__dict__[key], enum.Enum):
                    res[real_key] = self.__dict__[key].name
                elif isinstance(self.__dict__[key], datetime):
                    t = self.__dict__[key]
                    t = t.replace(tzinfo=timezone.utc)
                    res[real_key] = int(t.timestamp())
                else:
                    res[real_key] = self.__dict__[key]

        return res
