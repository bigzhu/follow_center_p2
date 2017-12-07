#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("../../lib_py")
import db_bz
from model import God
# from model import Message
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import cast

session = db_bz.session


def getGods(type, god_name):
    '''
    '''
    q = session.query(God).filter(getattr(God, type).isnot(None)
                                  ).filter(getattr(God, type)['name'] != cast("", JSONB))
    if god_name:
        q = q.filter(God.name == god_name)
    return q.all()


def loop(func, type, god_name=None, wait=None, test=False):
    '''
    create by bigzhu at 16/05/30 13:26:38 取出所有的gods，同步
    >>> loop('bigzhu', None, True)
    [<model.God object at ...>]
    '''

    gods = getGods(type, god_name)
    if test:
        return gods

    for god_info in gods:
        func(god_info, wait)
        session.commit()


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
