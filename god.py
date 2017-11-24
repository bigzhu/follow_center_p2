#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import db_bz
from sqlalchemy import and_, func, tuple_
from model import God, FollowWho, Remark
session = db_bz.getSession()


def addUserFollowedInfo(sub_sql, user_id):
    '''
    某用户是否关注
    >>> sub_sql = session.query(God).subquery()
    >>> addUserFollowedInfo(sub_sql, '4')
    <sqlalchemy.sql.selectable.Alias at...
    '''
    followed_info = session.query(FollowWho.god_id.label('followed_god_id'), FollowWho.updated_at.label(
        'followed_at'), FollowWho.id.label('followed')).filter(FollowWho.user_id == user_id).subquery()

    return session.query(sub_sql, followed_info.c.followed, followed_info.c.followed_at).outerjoin(
        followed_info,
        sub_sql.c.id == followed_info.c.followed_god_id).subquery()


def addAdminRemark(sub_sql):
    '''
    添加 remark 信息, 以最小的 user_id 的 remark 做其 admin remark
    >>> sub_sql = session.query(God).subquery()
    >>> addAdminRemark(sub_sql)
    <sqlalchemy.sql.selectable.Alias at...
    '''
    min_user_god = session.query(
        func.min(Remark.user_id), Remark.god_id).group_by(Remark.god_id).subquery()
    one_god_remark = session.query(Remark.remark, Remark.god_id).filter(
        tuple_(Remark.user_id, Remark.god_id).in_(min_user_god)).subquery()

    return session.query(sub_sql, one_god_remark.c.remark).outerjoin(
        one_god_remark,
        sub_sql.c.id == one_god_remark.c.god_id).subquery()


def addGodFollowedCount(sub_sql):
    '''
    添加每个god有多少人关注
    >>> sub_sql = session.query(God).subquery()
    >>> addGodFollowedCount(sub_sql)
    <sqlalchemy.sql.selectable.Alias at...
    '''
    god_count = session.query(
        func.count(FollowWho.id).label('count'), FollowWho.god_id).group_by(FollowWho.god_id).subquery()

    return session.query(sub_sql, god_count.c.count).outerjoin(
        god_count,
        sub_sql.c.id == god_count.c.god_id).subquery()


def filterAllNullGod(sub_sql):
    '''
    所有 social 都是空的废 god
    '''
    null_god = session.query(God.id).filter(
        and_(
            God.tumblr.is_(None), God.twitter.is_(None),
            God.github.is_(None), God.instagram.is_(None)))
    # 空的不查
    return session.query(sub_sql).filter(~sub_sql.c.id.in_(null_god)).subquery()


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
