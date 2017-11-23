#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
create by bigzhu at 15/07/04 22:25:30 取twitter的最新信息
modify by bigzhu at 15/07/17 16:49:58 添加pytz来修正crated_at的时区
modify by bigzhu at 15/07/17 17:08:38 存进去还是不对,手工来来修正吧
modify by bigzhu at 15/11/28 11:36:18 可以查某个用户
'''
import sys
sys.path.append("../lib_p_bz")
import god_oper
import sys
import datetime
import time_bz
import requests
import social_sync
requests.adapters.DEFAULT_RETRIES = 5
import time
from public_bz import storage
from db_bz import pg
import json
import public_bz
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

from socket import error as SocketError
import errno

M_TYPE = 'instagram'


def saveGraphqlMessage(ins_name, user_name, god_id, message):
    '''
    用 Graphql 取到的数据
    '''
    message = storage(message)

    m = public_bz.storage()
    m.god_name = user_name
    m.name = ins_name
    m.m_type = 'instagram'
    m.id_str = message.id
    m.created_at = time_bz.timestampToDateTime(message.taken_at_timestamp)

    if message.get('edge_media_to_caption').get('edges'):
        m.text = message.get('edge_media_to_caption').get('edges')[0].get('node').get('text')
    else:
        m.text = None
    m.extended_entities = json.dumps({'url': message.display_url})

    m.href = 'https://www.instagram.com/p/%s/' % message.shortcode
    if message.__typename == 'GraphSidecar':  # mutiple image
        edges = getMutipleImage(message.shortcode)
        images = []
        for edge in edges:
            url = edge['node']['display_url']
            images.append({'url': url})
        m.extended_entities = json.dumps(images)
        m.type = 'images'
    elif message.is_video:
        m.type = 'video'
        video_url = getVideoUrl(m.href)
        m.extended_entities = json.dumps({'url': message.display_url, 'video_url': video_url})
    else:
        m.type = 'image'
    id = pg.insertIfNotExist('message', m, "id_str='%s' and m_type='instagram'" % m.id_str)
    if id is not None:
        print '%s new instagram message %s' % (m.name, m.id_str)
    # 肯定会有一条重复
    # else:
    #    print '%s 重复记录 %s' % (m.user_name, m.id_str)
    return id


def getAllMedia(god_name):
    god = social_sync.getSocialGods('instagram', god_name)[0]
    god_name = god.name
    god_id = god.id
    ins_name = god.instagram['name']
    ins_id = god.instagram['id']
    url = 'https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={"id":"%s","first":1000}' % ins_id
    r = requests.get(url)
    if r.status_code == 200:
        nodes = r.json()['data']['user']['edge_owner_to_timeline_media']['edges']
        for node in nodes:
            node = node['node']
            saveGraphqlMessage(ins_name, god_name, god_id, node)
    else:
        print r.status_code


class CodeException(Exception):
    pass


def getVideoUrl(url):
    '''
    从 video 类型的网址中得到真实的 mp4 url 地址
    '''
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        videos = soup.find_all('meta', property='og:video')
        if (videos):
            return videos[0]['content']
    else:
        raise CodeException('getVideoUrl 异常: %s' % r.status_code)


def getMutipleImage(code):
    '''
    有多图时, 取多图
    '''
    url = "https://www.instagram.com/p/%s" % code
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        scripts = soup.find_all("script", type="text/javascript")
        for script in scripts:
            if '_sharedData' in str(script):
                content = script.contents[0]
                content = content.replace('window._sharedData =', '')
                content = content.replace(';', '')
                content = json.loads(content)
                edges = content['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
                return edges
    return None


def sync(god):
    '''
    create by bigzhu at 16/06/12 16:19:09 api disabled
    '''

    ins_name = god.instagram['name']
    god_name = god.name
    etag = god.instagram.get('sync_key')
    headers = {'If-None-Match': etag}
    url = "https://www.instagram.com/%s" % ins_name

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        etag = r.headers.get('etag')
        soup = BeautifulSoup(r.text)
        scripts = soup.find_all("script", type="text/javascript")
        for script in scripts:
            if '_sharedData' in str(script):
                if script.contents is None:
                    return
                content = script.contents[0]
                content = content.replace('window._sharedData =', '')
                content = content.replace(';', '')
                content = json.loads(content)
                user_info = content['entry_data']['ProfilePage'][0]['user']

                saveUser(god_name, ins_name, user_info, etag)
                if user_info['media'].get('nodes'):
                    for message in user_info['media']['nodes']:
                        saveMessage(ins_name, god_name, god.id, message)
    elif r.status_code == 304:
        pass
    elif r.status_code == 404:
        god_oper.delNoName(M_TYPE, god_name)
    else:
        print r.status_code
    # oper.noMessageTooLong(M_TYPE, user.instagram)


def saveUser(god_name, ins_name, user, sync_key):
    social_user = public_bz.storage()
    social_user.type = 'instagram'
    # social_user.name = user['username']
    social_user.name = ins_name
    social_user.count = user['followed_by']['count']
    social_user.avatar = user['profile_pic_url']
    social_user.description = user['biography']
    social_user.id = user['id']
    social_user.sync_key = sync_key
    pg.update('god', where={'name': god_name}, instagram=json.dumps(social_user))
    return social_user


def saveMessage(ins_name, user_name, god_id, message):
    '''
    create by bigzhu at 16/04/06 19:46:10
    '''
    message = storage(message)

    m = public_bz.storage()
    m.god_name = user_name
    m.name = ins_name
    m.m_type = 'instagram'
    m.id_str = message.id
    m.created_at = time_bz.timestampToDateTime(message.date)
    if message.get('caption'):
        m.text = message.caption
    else:
        m.text = None
    m.extended_entities = json.dumps({'url': message.display_src})
    m.href = 'https://www.instagram.com/p/%s/' % message.code
    if message.__typename == 'GraphSidecar':  # mutiple image
        edges = getMutipleImage(message.code)
        if not edges:
            return
        images = []
        for edge in edges:
            url = edge['node']['display_url']
            images.append({'url': url})
        m.extended_entities = json.dumps(images)
        m.type = 'images'
    elif message.is_video:
        m.type = 'video'
        video_url = getVideoUrl(m.href)
        m.extended_entities = json.dumps({'url': message.display_src, 'video_url': video_url})
    else:
        m.type = 'image'
    id = pg.insertIfNotExist('message', m, "id_str='%s' and m_type='instagram'" % m.id_str)
    if id is not None:
        print '%s new instagram message %s' % (m.name, m.id_str)
    # 肯定会有一条重复
    # else:
    #    print '%s 重复记录 %s' % (m.user_name, m.id_str)
    return id


def loop(god_name=None):
    gods = social_sync.getSocialGods('instagram', god_name)
    for god in gods:
        sync(god)


def main():
    if len(sys.argv) == 3:
        god_name = (sys.argv[1])
        if sys.argv[2] == 'all':
            getAllMedia(god_name)
        exit(0)
    if len(sys.argv) == 2:
        user_name = (sys.argv[1])
        loop(user_name)
        exit(0)
    while True:
        try:
            loop()
        except CodeException as e:
            print e
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise  # Not error we are looking for
            print e
        except ConnectionError as e:
            print e
        except ValueError as e:
            print e
        except requests.exceptions.ChunkedEncodingError as e:
            print e
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(1200)


if __name__ == '__main__':
    main()
    # import doctest
    # doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
