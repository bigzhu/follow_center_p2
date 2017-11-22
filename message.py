#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
message 表的一些操作
'''
import sys
sys.path.append("../lib_py")
import db_bz
from db_bz import session_for_get as session
import filter_oper

all_message = db_bz.getReflect('all_message')


def getUnreadCount(user_id, after):
    '''
    查出某用户未, 基于某时间的未读数
    >>> import datetime
    >>> tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    >>> getUnreadCount('4', tomorrow)
    0
    '''

    unread_query = filter_oper.filterFollowedMessage(
        all_message, user_id)
    unread_query = session.query(unread_query).filter(
        unread_query.c.out_created_at > after).subquery()
    unread_message_count = session.query(unread_query).count()
    return unread_message_count


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
