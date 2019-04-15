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

from .sqlalchemy_base import Base


class User(Base):
    """用户"""
    __tablename__ = 'user'

    user_id = Column(Integer)
    name = Column(String(30))
    phone = Column(String(100))
    password = Column(String(36))
    avatar = Column(String(255))
    remark = Column(Text)
    deleted = Column(SmallInteger, server_default=text('0'))

    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP  ON UPDATE CURRENT_TIMESTAMP'))

    __table_args__ = (
        PrimaryKeyConstraint('user_id'),
        Index('ix_user_phone', phone),
        Index('ix_user_name', name),
        Index('ix_user_password', password),
        {
            'mysql_engine': 'InnoDB'
        },
    )
