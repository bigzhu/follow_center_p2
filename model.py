#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")
import datetime
from sqlalchemy import Column, ForeignKey, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
import model_bz


class AnkiSave(model_bz.Base):
    '''
    标记是否发到anki
    >>> AnkiSave.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'anki_save'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Text, nullable=False)

    message_id = Column(Integer, ForeignKey('message.id'), nullable=False)


class God(model_bz.Base):
    '''
    god 的信息 create by bigzhu at 16/05/24 10:01:39
    modify by bigzhu at 17/05/19 19:16:08 改为用 json 放社交信息
    >>> God.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'god'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    name = Column(Text, nullable=False)  # 名字
    bio = Column(Text)  # 说明
    twitter = Column(JSONB, nullable=False)  #
    github = Column(JSONB, nullable=False)  #
    instagram = Column(JSONB, nullable=False)  #
    tumblr = Column(JSONB, nullable=False)  #
    facebook = Column(JSONB, nullable=False)  #
    cat = Column(Text)  # 说明
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_public = Column(Integer, default=0)  # 是不是可以看到的，如果是，那么cat不能改
    is_black = Column(Integer, default=0)  # 是否黑名单


class Message(model_bz.Base):
    '''
    社交信息
    create by bigzhu at 16/03/25 14:52:27 冗余存放数据，提高效率
    >>> Message.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    god_id = Column(Integer)  # 实际上是你要follow的用户的id
    god_name = Column(Text)  # 在本系统的主户名
    name = Column(Text, nullable=False)  # 在社交帐号的名字

    out_id = Column(Text, nullable=False)  # 外部的id, 避免重复同步 以前叫 id_str
    m_type = Column(Text, nullable=False)  # twitter or instagram or github
    out_created_at = Column(DateTime)  # 在对应社交帐号真实的生成时间 以前的 created_at
    content = Column(JSONB)  # 带结构的内容
    text = Column(Text)  # 文本内容
    title = Column(Text)  # tumblr text blog 的 title
    extended_entities = Column(JSONB)  # 扩展内容,图片什么
    href = Column(Text)  # message 的link
    type = Column(Text)  # media type


class Collect(model_bz.Base):
    '''
    收藏的 message
    >>> Collect.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'collect'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Text, nullable=False)
    message_id = Column(Integer, ForeignKey('message.id'), nullable=False)


class Last(model_bz.Base):
    '''
    上次看到那条 message 的时间
    >>> Last.__table__.create(checkfirst=True)
    '''
    __tablename__ = 'last'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Text, nullable=False)


class Anki(model_bz.Base):
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


def createNeed():
    '''
    建立要用的表
    >>> createNeed()
    '''
    model_bz.OauthInfo.__table__.create(checkfirst=True)
    Anki.__table__.create(checkfirst=True)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
