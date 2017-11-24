#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
message 表的一些操作
'''
import sys
sys.path.append("../lib_py")
import db_bz
from model import AnkiSave, Collect, God, FollowWho

all_message = db_bz.getReflect('all_message')
session = db_bz.session


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


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
