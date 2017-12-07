#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import db_bz
import model
import message_oper
from db_bz import session
all_message = db_bz.getReflect('all_message')
from sqlalchemy import and_


def deleteCollect(message_id, user_id):
    count = session.query(model.Collect).filter(and_(
        model.Collect.message_id == message_id, model.Collect.user_id == user_id)).delete()
    if count != 1:
        raise Exception('没有正确的uncollect, uncollect %s 条' % count)


def getCollect(user_id):
    '''
    >>> getCollect('4')
    '''
    sub_sql = session.query(all_message).subquery()
    sub_sql = message_oper.addCollectInfo(sub_sql, user_id)
    sub_sql = message_oper.addAnkiInfo(sub_sql, user_id)
    messages = session.query(sub_sql).filter(
        ~sub_sql.c.collect.is_(None)).order_by(sub_sql.c.collect_at).all()
    return [r._asdict() for r in messages]


def collect(message_id, user_id):
    '''
    create by bigzhu at 16/05/20 14:21:02 加入收藏
    >>> collect(1, '4')
    (<model.Collect object at ...>, True)
    '''
    collect, is_insert = db_bz.getOrInsert(model.Collect, {
                                           'user_id': user_id, 'message_id': message_id}, user_id=user_id, message_id=message_id)
    return collect, is_insert


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
