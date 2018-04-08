#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
message 表的一些操作
'''
import sys
sys.path.append("../lib_py")
import db_bz
from model import AnkiSave, Collect
from db_bz import session
import model
import time_bz
import datetime
from model import God
from model import FollowWho
from sqlalchemy import or_
from sqlalchemy import desc
from model import Message

all_message = db_bz.getReflect('all_message')


def getByID(user_id, id):
    sub_sql = session.query(all_message).filter(
        all_message.c.id == id).subquery()
    print(sub_sql)
    if user_id:
        sub_sql = addCollectInfo(sub_sql, user_id)
        sub_sql = addAnkiInfo(sub_sql, user_id)
    message = session.query(sub_sql).one_or_none()
    return message._asdict()


def getOld(user_id, before, limit, search_key, god_name, not_types):
    sub_sql = session.query(all_message).subquery()
    if not_types:
        sub_sql = session.query(sub_sql).filter(
            ~sub_sql.c.m_type.in_(not_types)).subquery()
    if user_id:
        sub_sql = addCollectInfo(sub_sql, user_id)
        sub_sql = addAnkiInfo(sub_sql, user_id)
    else:  # 不给看18+
        sub_sql = session.query(all_message).filter(
            all_message.c.cat != '18+').subquery()
        # 只要 public 的
        sub_sql = session.query(sub_sql).filter(
            sub_sql.c.god_name.in_(
                session.query(God.name).filter(God.is_public.in_(
                    [1, 2])))).subquery()

    # 查这个时间前的
    before = time_bz.jsonToDatetime(before)
    last = session.query(model.Last).filter(model.Last.id == 1).one()
    last.updated_at = before
    session.commit()

    sub_sql = session.query(sub_sql).filter(
        sub_sql.c.out_created_at < before).subquery()

    if god_name:
        sub_sql = session.query(sub_sql).filter(
            sub_sql.c.god_name == god_name).subquery()
    elif search_key:
        # jsonb 没找到办法做like
        #query = session.query(query).filter(or_(query.c.text.ilike('%%%s%%' % search_key), query.c.content.astext.like('%%%s%%' % search_key))).subquery()
        sub_sql = session.query(sub_sql).filter(
            or_(sub_sql.c.text.ilike('%%%s%%' % search_key))).subquery()
    elif user_id:
        sub_sql = filterFollowed(sub_sql, user_id)

    messages = session.query(sub_sql).order_by(
        desc(sub_sql.c.out_created_at)).limit(limit).all()
    messages = [r._asdict() for r in messages]
    return messages


def getNew(user_id, after, limit, search_key, god_name, not_types):
    unread_message_count = 0

    if after:
        after = time_bz.jsonToDatetime(after)

    if search_key is None and god_name is None:  # 不按 search 和 god 查时, 登录了取 last
        if after is None:
            after = session.query(model.Last.updated_at).filter(
                model.Last.user_id == user_id).one_or_none()
        if after is None:  # 未登录或者没有last, 取最近两天
            after = datetime.date.today() - datetime.timedelta(days=6)

    sub_sql = session.query(all_message).subquery()
    if not_types:
        sub_sql = session.query(sub_sql).filter(
            ~sub_sql.c.m_type.in_(not_types)).subquery()

    if user_id:
        sub_sql = addCollectInfo(sub_sql, user_id)
        sub_sql = addAnkiInfo(sub_sql, user_id)
    else:
        # 不要 18+ 的
        sub_sql = session.query(all_message).filter(
            all_message.c.cat != '18+').subquery()
        # 只要 public 的
        sub_sql = session.query(sub_sql).filter(
            sub_sql.c.god_name.in_(
                session.query(God.name).filter(God.is_public.in_(
                    [1, 2])))).subquery()

    # after = None
    # 查比这个时间新的
    if after:
        sub_sql = session.query(sub_sql).filter(
            sub_sql.c.out_created_at > after).subquery()

    # 互斥的filter_bz.filter
    if god_name:
        sub_sql = session.query(sub_sql).filter(
            sub_sql.c.god_name == god_name).subquery()
    elif search_key:
        # jsonb 没找到办法做like
        #query = session.query(query).filter(or_(query.c.text.ilike('%%%s%%' % search_key), query.c.content.astext.like('%%%s%%' % search_key))).subquery()
        sub_sql = session.query(sub_sql).filter(
            or_(sub_sql.c.text.ilike('%%%s%%' % search_key))).subquery()
    elif user_id:  # 没那几个, 又有 user_id, 只查关注了的
        sub_sql = filterFollowed(sub_sql, user_id)
        if after:
            # 查出还有多少未读
            unread_message_count = getUnreadCount(user_id, after)

    sub_sql = session.query(sub_sql).order_by(
        sub_sql.c.out_created_at).limit(limit)
    #print(sub_sql)
    messages = sub_sql.all()

    messages = [r._asdict() for r in messages]
    data = dict(
        messages=messages, unread_message_count=unread_message_count)

    return data


def filterFollowed(sub_sql, user_id):
    '''
    查出这个用户关注的, 返回 subquery
    >>> import db_bz
    >>> all_message = db_bz.getReflect('all_message')
    >>> sub_sql = session.query(all_message).subquery()
    >>> query = filterFollowed(all_message, '1')
    >>> session.query(sub_sql).count()
    1...
    '''
    query = session.query(sub_sql).filter(
        sub_sql.c.god_name.in_(
            session.query(God.name).filter(
                God.id.in_(
                    session.query(FollowWho.god_id).filter(
                        FollowWho.user_id == user_id))))).subquery()

    return query


def addCollectInfo(sub_sql, user_id):
    '''
    把收藏信息附加到 message
    '''
    # 取出这个用户的收藏
    collect_sq = session.query(Collect).filter(
        Collect.user_id == user_id).subquery()
    # 附加收藏到 message 里
    sql = session.query(
        sub_sql, collect_sq.c.message_id.label('collect'),
        collect_sq.c.created_at.label('collect_at')).outerjoin(
            collect_sq, sub_sql.c.id == collect_sq.c.message_id).subquery()
    return sql


def addAnkiInfo(sub_sql, user_id):
    '''
    把收藏信息附加到 message
    '''
    # 取出这个用户的anki
    anki_sq = session.query(AnkiSave).filter(
        AnkiSave.user_id == user_id).subquery()
    # 附加 anki 到 message
    return session.query(sub_sql, anki_sq.c.message_id.label('anki'),
                         anki_sq.c.created_at.label('anki_at')).outerjoin(
                             anki_sq,
                             sub_sql.c.id == anki_sq.c.message_id).subquery()


def getUnreadCount(user_id, after):
    '''
    查出某用户未, 基于某时间的未读数
    >>> import datetime
    >>> tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    >>> getUnreadCount('4', tomorrow)
    0
    '''

    unread_query = filterFollowed(
        all_message, user_id)
    unread_query = session.query(unread_query).filter(
        unread_query.c.out_created_at > after).subquery()
    unread_message_count = session.query(unread_query).count()
    return unread_message_count


def getNotUploadImageMessagesByMType(m_type):
    '''
    取出没有上载过的 image message
    '''
    messages = session.query(Message).filter(
        or_(Message.type == 'image', Message.type == 'images', Message.type == 'photo')
    ).filter(Message.m_type == m_type).filter(Message.images.is_(None)).all()
    return messages


if __name__ == '__main__':
    for i in getNotUploadImageMessagesByMType('instagram'):
        print(i.type)
    #import doctest
    #doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
