#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import db_bz
from db_bz import session
from model import FollowWho

from sqlalchemy import and_


def unFollow(user_id, god_id):
    '''
    取消关注
    >>> unFollow('4', 1)
    '''
    count = session.query(FollowWho).filter(
        and_(FollowWho.user_id == user_id, FollowWho.god_id == god_id)).delete()

    if count != 1:
        raise Exception('没有正确的Unfollow, Unfollow %s 人' % count)


def follow(user_id, god_id, make_sure=True):
    '''
    create by bigzhu at 15/07/15 14:22:51
    modify by bigzhu at 15/07/15 15:00:28 如果不用告警,就不要make_sure
    >>> follow('4', 1)
    '''
    f = dict(
        user_id=user_id,
        god_id=god_id
    )
    follow_who, is_insert = db_bz.getOrInsert(
        FollowWho, f, user_id=user_id, god_id=god_id)
    if not is_insert and make_sure:
        raise Exception('没有正确的Follow, 似乎已经Follow过了呢')


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
