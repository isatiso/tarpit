# coding:utf-8
"""Lazor Database Module."""
import uuid
import enum
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import (CHAR, BigInteger, Column, Enum, Integer, SmallInteger,
                        Text, String, Numeric, Float, TIMESTAMP)
from sqlalchemy.dialects.mysql import MEDIUMTEXT, INTEGER, DECIMAL
from sqlalchemy import PrimaryKeyConstraint, Sequence, UniqueConstraint, Index
from sqlalchemy import text

from .sqlalchemy_base import Base, CreatedAt, UpdatedAt, Remark, Deleted


class User(Base, CreatedAt, UpdatedAt, Remark, Deleted):
    """用户"""
    __tablename__ = 'user'

    user_id = Column(Integer)
    name = Column(String(30))
    phone = Column(String(100))
    password = Column(String(36))
    avatar = Column(String(255))

    __table_args__ = (
        PrimaryKeyConstraint('user_id'),
        Index('ix_user_phone', phone),
        Index('ix_user_name', name),
        Index('ix_user_password', password),
        {
            'mysql_engine': 'InnoDB'
        },
    )
