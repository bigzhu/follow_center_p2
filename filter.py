#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
一些复用的filter
'''

from model import God, FollowWho


def filterFollowedMessage(query, session, user_id):
    '''
    查出这个用户关注的, 返回 subquery
    >>> import db_bz
    >>> all_message = db_bz.getReflect('all_message')
    >>> session = db_bz.getSession()
    >>> query = filterFollowedMessage(all_message, session, '1')
    >>> session.query(query).count()
    '''
    query = session.query(query).filter(
        query.c.god_name.in_(
            session.query(God.name).filter(
                God.id.in_(
                    session.query(FollowWho.god_id).filter(
                        FollowWho.user_id == user_id))))).subquery()

    return query


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
