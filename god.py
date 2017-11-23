#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

from db_bz import session_for_get as session
from sqlalchemy import and_
from model import God


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
    #sql = session.query(God).subquery()
    #sql = filterAllNullGod(sql)
    #print(session.query(sql).count())
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
