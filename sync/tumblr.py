#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
create by bigzhu at 15/07/15 17:17:29 取github的动态
'''
import sys
sys.path.append("../lib_p_bz")

import datetime
import requests
import sys
from db_bz import pg
import json
import social_sync
import time_bz
import time
import public_bz
import god_oper
M_TYPE = 'tumblr'
API_KEY = 'w0qnSK6sUtFyapPHzZG7PjbTXbsYDoilrnmrblIbA56GTl0ULL'


class NoUser(Exception):
    pass


def getTumblrUserNotSaveKey(god_name, tumblr_name):
    blogs = callGetMeidaApi(god_name=tumblr_name, limit=1)
    if blogs is None:
        # public_db.sendDelApply('tumblr', god_name, tumblr_name, 'not have user')
        god_oper.delNoName('tumblr', god_name)
        return
    tumblr_user = blogs['response']['blog']
    tumblr_user['updated'] = None
    saveUser(god_name, tumblr_name, tumblr_user)


def getTumblrUser(god_name, tumblr_name, save=True):
    blogs = callGetMeidaApi(god_name=tumblr_name, limit=1)
    if blogs is None:
        # public_db.sendDelApply('tumblr', god_name, tumblr_name, 'not have user')
        god_oper.delNoName('tumblr', god_name)
        raise NoUser('%s blog is None' % tumblr_name)
    tumblr_user = blogs['response']['blog']
    if save:
        saveUser(god_name, tumblr_name, tumblr_user)
    return tumblr_user


def tumblrRealAvatar(url):
    '''
    create by bigzhu at 16/05/28 11:06:23 tumblr 用了 301 来转 avatar url,要再调一次
    '''
    r = requests.get(url)
    return r.url


def saveUser(god_name, tumblr_name, user):
    social_user = public_bz.storage()
    social_user.type = 'tumblr'
    # social_user.name = user['name']
    social_user.name = tumblr_name
    social_user.count = user.get('likes', -1)  # 有人会不分享likes数
    avatar_url = 'https://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/512' % user['name']
    social_user.avatar = tumblrRealAvatar(avatar_url)
    social_user.description = user['description']
    social_user.sync_key = user['updated']

    pg.update('god', where={'name': god_name}, tumblr=json.dumps(social_user))
    return social_user


def saveMessage(god_name, twitter_name, god_id, blog):
    m = public_bz.storage()
    m.god_id = god_id
    m.god_name = god_name
    m.name = twitter_name

    m.id_str = blog['id']
    m.m_type = 'tumblr'
    m.created_at = time_bz.timestampToDateTime(blog['timestamp'])
    type = blog.get('type')
    m.href = blog.get('short_url')
    m.type = type
    if type == 'text':
        m.title = blog.get('title')
        m.text = blog.get('body')
    elif type == 'photo':
        m.text = blog.get('caption')
        m.extended_entities = json.dumps(blog.get('photos'))
    elif type == 'video':
        m.extended_entities = json.dumps({'video_url': blog.get('video_url')})
    m.content = None

    id = pg.insertIfNotExist('message', m, "id_str='%s' and m_type='tumblr' " % m.id_str)
    if id is None:
        pass
    else:
        print '%s new tumblr message %s' % (m.name, m.id_str)


def getFollowedCount(tumblr_name):
    '''
    没成功, 取不到
    '''
    params = {'api_key': API_KEY,
              'blog-identifier': '%s.tumblr.com' % tumblr_name}
    url = '''http://api.tumblr.com/v2/blog/%s.tumblr.com/followers''' % tumblr_name
    r = requests.get(url, params=params)
    print r
    if r.status_code == 200:
        try:
            medias = r.json()
            return medias
        except Exception:
            print 'r=', r
            print public_bz.getExpInfoAll()
    print r.status_code


def callGetMeidaApi(god_name, offset=0, limit=20):
    params = {'api_key': API_KEY,
              'offset': offset,
              'limit': limit,
              }
    url = '''http://api.tumblr.com/v2/blog/%s.tumblr.com/posts''' % god_name
    r = requests.get(url, params=params)
    if r.status_code == 200:
        try:
            medias = r.json()
            return medias
        except Exception:
            print 'r=', r
            print public_bz.getExpInfoAll()
            return
    elif r.status_code == 429:
        raise Exception('达到最大访问次数')
    else:
        print r.status_code


def main(god, wait):
    god_name = god.name
    tumblr_name = god.tumblr['name']
    god_id = god.id
    tumblr_user = getTumblrUser(god_name, tumblr_name, False)

    if tumblr_user['updated'] == god.tumblr.get('sync_key'):
        pass
    else:
        # 只取最新的20条来保存
        blogs = callGetMeidaApi(god_name=tumblr_name, limit=200)['response']['posts']
        for message in blogs:
            saveMessage(god_name, tumblr_name, god_id, message)
        # oper.noMessageTooLong(M_TYPE, tumblr_name)
    saveUser(god_name, tumblr_name, tumblr_user)


def loop(god_name=None, wait=None):
    '''
    '''
    gods = social_sync.getSocialGods('tumblr', god_name)
    for god in gods:
        main(god, wait)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(god_name)
        exit(0)
    while True:
        try:
            loop(wait=True)
        except requests.exceptions.ConnectionError:
            print public_bz.getExpInfoAll()
        except requests.exceptions.ChunkedEncodingError as e:
            print e
        except requests.exceptions.ReadTimeout as e:
            print e
        except NoUser as e:
            print e
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(1200)
