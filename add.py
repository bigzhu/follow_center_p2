#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
附件信息
'''
from db_bz import session_for_get as session
from model import God, Collect


def addCollectMessage(sub_sql, user_id):
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
            collect_sq,
            sub_sql.c.id == collect_sq.c.message_id).subquery()
    return sql


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
