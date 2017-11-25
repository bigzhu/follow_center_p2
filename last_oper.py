#!/usr/bin/env python
# -*- coding: utf-8 -*-

import db_bz
from model import Last


def saveLast(user_id, last):
    last_info = dict(updated_at=last)
    db_bz.updateOrInsert(Last, last_info, user_id=user_id)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
