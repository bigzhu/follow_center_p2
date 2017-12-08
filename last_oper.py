#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model import Last
from db_bz import session


def saveLast(user_id, last):
    # last_info = dict(updated_at=last)
    last_info = session.query(Last).filter(
        Last.updated_at < last).filter(Last.user_id == user_id).one_or_none()
    if last_info is not None:
        last_info.updated_at = last


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
