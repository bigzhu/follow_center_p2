#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
create by bigzhu at 15/07/15 17:17:29 取github的动态
'''
import sys
sys.path.append("../../lib_py")
sys.path.append("../")

import datetime
import requests
import exception_bz
import db_bz
from model import Message
import sys
import json
import time
M_TYPE = 'tumblr'
API_KEY = 'w0qnSK6sUtFyapPHzZG7PjbTXbsYDoilrnmrblIbA56GTl0ULL'
from .social_lib import loop


def syncUserInfo(god):
    '''
    同步用户信息
    '''
    tumblr_name = god.tumblr['name']
    blogs = callGetMeidaApi(tumblr_name, limit=1)
    if blogs is None:
        # public_db.sendDelApply('tumblr', god_name, tumblr_name, 'not have user')
        # god_oper.delNoName('tumblr', god_name)
        raise NoUser('%s blog is None' % tumblr_name)
    tumblr_user = blogs['response']['blog']
    if tumblr_user['updated'] == god.tumblr.get('sync_key'):
        raise NoChange('%s no change' % tumblr_name)
    else:
        avatar_url = 'https://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/512' % tumblr_user['name']
        tumblr = dict(
            type='tumblr',
            name=god.tumblr['name'],
            count=tumblr_user.get('likes', -1),  # 有人会不分享likes数
            avatar=tumblrRealAvatar(avatar_url),
            description=tumblr_user['description'],
            sync_key=tumblr_user['updated']
        )
        god.tumblr = tumblr


class NoChange(Exception):
    pass


class NoUser(Exception):
    pass


def tumblrRealAvatar(url):
    '''
    create by bigzhu at 16/05/28 11:06:23 tumblr 用了 301 来转 avatar url,要再调一次
    '''
    r = requests.get(url)
    return r.url


def saveMessage(god_name, tumblr_name, god_id, blog):
    m = dict(
        god_id=god_id,
        god_name=god_name,
        name=tumblr_name,
        out_id=str(blog['id']),
        m_type='tumblr',
        created_at=datetime.datetime.utcfromtimestamp(blog['timestamp']),
        href=blog.get('short_url')
    )
    type = blog.get('type')
    m['type'] = type
    if type == 'text':
        m['title'] = blog.get('title')
        m['text'] = blog.get('body')
    elif type == 'photo':
        m['text'] = blog.get('caption')
        m['extended_entities'] = json.dumps(blog.get('photos'))
    elif type == 'video':
        m['extended_entities'] = json.dumps(
            {'video_url': blog.get('video_url')})
    m['content'] = None

    i, insert = db_bz.updateOrInsert(
        Message, m, out_id=str(blog['id']), m_type='tumblr')
    if insert:
        print('%s new tumblr %s' % (m['name'], m['out_id']))


def callGetMeidaApi(tumblr_name, offset=0, limit=20):
    params = {'api_key': API_KEY,
              'offset': offset,
              'limit': limit,
              }
    url = '''http://api.tumblr.com/v2/blog/%s.tumblr.com/posts''' % tumblr_name
    r = requests.get(url, params=params)
    if r.status_code == 200:
        try:
            medias = r.json()
            return medias
        except Exception:
            print ('r=', r)
            print (exception_bz.getExpInfoAll())
            return
    elif r.status_code == 429:
        raise Exception('达到最大访问次数')
    else:
        print(r.status_code)


def sync(god, wait):
    god_name = god.name
    tumblr_name = god.tumblr['name']
    god_id = god.id
    try:
        syncUserInfo(god)
    except NoChange as e:
        print(e)
        return
    except NoUser as e:
        print(e)
        return
    # 只取最新的200条来保存
    messages = callGetMeidaApi(tumblr_name, limit=200)[
        'response']['posts']
    for message in messages:
        saveMessage(god_name, tumblr_name, god_id, message)


def main():
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(sync, 'tumblr', god_name)
        exit(0)
    while True:
        try:
            loop(sync, 'tumblr', wait=True)
        except requests.exceptions.ConnectionError:
            print(exception_bz.getExpInfoAll())
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
        except requests.exceptions.ReadTimeout as e:
            print(e)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1200)


if __name__ == '__main__':
    main()
