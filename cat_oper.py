#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

from model import FollowWho
from model import God
from sqlalchemy import func
import god_oper
from db_bz import session


def getCat(user_id, followed=False):
    q = session.query(God)
    if followed:
        my_god = session.query(
            FollowWho.god_id).filter(FollowWho.user_id == user_id)
        q = q.filter(God.id.in_(my_god))
    else:
        q = q.filter(God.is_public == 1)
        if user_id is None:
            q = q.filter(God.cat != '18+')

    sub_sql = god_oper.filterAllNullGod(q.subquery())
    sub_sql = god_oper.addGodFollowedCount(sub_sql)

    data = session.query(
        func.count(sub_sql.c.cat).label('count'), sub_sql.c.cat).group_by(
            sub_sql.c.cat).all()

    data = [r._asdict() for r in data]
    return data


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
