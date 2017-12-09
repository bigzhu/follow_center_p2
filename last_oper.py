#!/usr/bin/env python
# -*- coding: utf-8 -*-

from model import Last
from db_bz import session


def saveLast(user_id, last):
    # last_info = dict(updated_at=last)
    '''
    >>> import datetime
    >>> now = datetime.datetime.utcnow()
    >>> saveLast('6', now)
    '''
    last_info = session.query(Last).filter(Last.user_id == user_id).one_or_none()
    if last_info is not None:
        if last_info.updated_at < last:
            last_info.updated_at = last
    else:
        last_info = Last(user_id=user_id, updated_at=last)
        session.add(last_info)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
