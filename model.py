#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")
import datetime
from sqlalchemy import Column, Integer, Text, DateTime

from model_bz import Base


class Anki(Base):

    '''
    anki 的登录信息
    >>> Anki.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'anki'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # 建立时间
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)  # update 时间

    user_id = Column(Text, nullable=False)
    user_name = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    csrf_token = Column(Text)
    mid = Column(Text)
    cookie = Column(Text)


if __name__ == '__main__':
    Anki.__table__.drop(checkfirst=True)
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
