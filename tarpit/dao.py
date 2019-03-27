# coding:utf-8
from functools import wraps
import traceback
import enum
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query, Session
from motor import MotorGridFSBucket, motor_tornado as motor
from pymongo import MongoClient

from .utils.logger import dump_in, dump_out, dump_error
from .config import CONFIG as O_O


class MongoBase():
    """Mongo Client Set."""

    __collection_name__ = None
    __alias__ = None

    def __init__(self):
        T_T = O_O.database.mongo
        self.client = motor.MotorClient(T_T.client).__getattr__(T_T.db)
        self.sync_client = MongoClient(T_T.client).__getattr__(T_T.db)
        self.__setattr__(self.__collection_name__,
                         self.client.__getattr__(self.__collection_name__))

    def __collection_init__(self):
        """Write some collection initial operation, like set some index."""
        pass


class MongoFactory():
    """Mongo Client Set."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoFactory, cls).__new__(cls)
            cls._instance.mongo_init()
            print('mongo new')

        return cls._instance

    @classmethod
    def mongo_init(self):
        self.collection_dict = {(scls.__alias__ or scls.__collection_name__):
                                scls for scls in MongoBase.__subclasses__()}
        for scls in MongoBase.__subclasses__():
            scls().__collection_init__()

    def __getattr__(self, name):
        return self.collection_dict[name]()


class SessionMaker:

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SessionMaker, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.new_engine = create_engine(
            O_O.database.mysql,
            echo=False,
            pool_recycle=1000,
            encoding='utf-8',
            isolation_level='REPEATABLE_READ')
        self.session_maker = sessionmaker(bind=self.new_engine)

    def create(self):
        return self.session_maker()


class BaseMapper:
    """Base Mapper."""

    __alias__ = None

    def __init__(self, session):
        if not isinstance(session, Session):
            raise ValueError(
                "session is not instance of sqlalchemy.orm.session.Session.")
        self.session = session


class DaoContext:

    def __init__(self, session, mapper):
        self.session = session
        self.mapper = mapper

    def get_mapper(self):
        return self.mapper(self.session)

    def commit(self):
        self.session.commit()

    def dict_of(self, entity, *options, **alias):
        if entity is None:
            return dict()

        res = dict()
        for key in options:
            alias[key] = None

        for key in entity.__dict__:
            if not alias or key in alias:
                if not key.startswith('_'):
                    if isinstance(alias.get(key), str):
                        real_key = alias[key]
                    else:
                        real_key = key
                    if isinstance(entity.__dict__[key], enum.Enum):
                        res[real_key] = entity.__dict__[key].name
                    elif isinstance(entity.__dict__[key], datetime):
                        t = entity.__dict__[key]
                        t = t.replace(tzinfo=timezone.utc)
                        res[real_key] = int(t.timestamp())
                    else:
                        res[real_key] = entity.__dict__[key]

        return res


def transaction(function, mappers, rollback=True):
    """Wrap a handle shell to a query function."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        """Function that wrapped."""
        session = SessionMaker().create()
        if mappers:
            mapper_dict = {(scls.__alias__ or scls.__name__): scls
                           for scls in BaseMapper.__subclasses__()}
            parents = tuple(mapper_dict[m] for m in mappers if m in mapper_dict)
            mapper = type('Mapper', parents, {})
        else:
            mapper = BaseMapper

        context = DaoContext(session, mapper)

        try:
            return function(context, *args, **kwargs)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    return wrapper