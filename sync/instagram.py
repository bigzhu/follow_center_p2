#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
create by bigzhu at 15/07/04 22:25:30 取twitter的最新信息
modify by bigzhu at 15/07/17 16:49:58 添加pytz来修正crated_at的时区
modify by bigzhu at 15/07/17 17:08:38 存进去还是不对,手工来来修正吧
modify by bigzhu at 15/11/28 11:36:18 可以查某个用户
'''
import sys
sys.path.append("../../lib_py")
sys.path.append("../")
# import god_oper
import sys
import datetime
import time_bz
import requests
requests.adapters.DEFAULT_RETRIES = 5
import time
import json
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

from socket import error as SocketError
import errno
from social_lib import loop
from social_lib import getGods
from model import Message
import db_bz

M_TYPE = 'instagram'


def saveGraphqlMessage(ins_name, user_name, god_id, message):
    '''
    用 Graphql 取到的数据
    '''
    m = dict(
        god_name=user_name,
        name=ins_name,
        m_type='instagram',
        out_id=message['id'],
        out_created_at=time_bz.timestampToDateTime(
            message['taken_at_timestamp'])
    )

    if message.get('edge_media_to_caption').get('edges'):
        m['text'] = message.get('edge_media_to_caption').get(
            'edges')[0].get('node').get('text')
    else:
        m['text'] = None
    m['extended_entities'] = {'url': message['display_url']}

    m['href'] = 'https://www.instagram.com/p/%s/' % message['shortcode']
    if message['__typename'] == 'GraphSidecar':  # mutiple image
        edges = getMutipleImage(message['shortcode'])
        images = []
        for edge in edges:
            url = edge['node']['display_url']
            images.append({'url': url})
        m['extended_entities'] = images
        m['type'] = 'images'
    elif message['is_video']:
        m['type'] = 'video'
        video_url = getVideoUrl(m['href'])
        m['extended_entities'] = {
            'url': message['display_url'], 'video_url': video_url}
    else:
        m['type'] = 'image'

    i, insert = db_bz.updateOrInsert(
        Message, m, out_id=message['id'], m_type='instagram')
    if insert:
        print('%s new instagram %s' % (m['name'], m['out_id']))


def getAllMedia(god_name):
    god = getGods('instagram', god_name)[0]
    god_name = god.name
    god_id = god.id
    ins_name = god.instagram['name']
    ins_id = god.instagram['id']
    url = 'https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={"id":"%s","first":1000}' % ins_id
    r = requests.get(url)
    if r.status_code == 200:
        nodes = r.json()[
            'data']['user']['edge_owner_to_timeline_media']['edges']
        for node in nodes:
            node = node['node']
            saveGraphqlMessage(ins_name, god_name, god_id, node)
    else:
        print(r.status_code)


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


def sync(god, wait):
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
                user = content['entry_data']['ProfilePage'][0]['user']

                saveUser(god, user, etag)
                if user['media'].get('nodes'):
                    for message in user['media']['nodes']:
                        saveMessage(ins_name, god_name, god.id, message)
    elif r.status_code == 304:
        pass
    elif r.status_code == 404:
        print(r.status_code)
        # god_oper.delNoName(M_TYPE, god_name)
    else:
        print(r.status_code)
    # oper.noMessageTooLong(M_TYPE, user.instagram)


def saveUser(god, user, sync_key):

    ins_name = god.instagram['name']
    instagram = dict(
        type='instagram',
        name=ins_name,
        count=user['followed_by']['count'],
        avatar=user['profile_pic_url'],
        description=user['biography'],
        id=user['id'],
        sync_key=sync_key
    )
    god.instagram = instagram
    return True


def saveMessage(ins_name, user_name, god_id, message):
    '''
    create by bigzhu at 16/04/06 19:46:10
    '''

    m = dict(
        god_name=user_name,
        name=ins_name,
        m_type='instagram',
        out_id=message['id'],
        out_created_at=time_bz.timestampToDateTime(message['date'])
    )
    if message.get('caption'):
        m['text'] = message['caption']
    else:
        m['text'] = None
    m['extended_entities'] = {'url': message['display_src']}
    m['href'] = 'https://www.instagram.com/p/%s/' % message['code']
    if message['__typename'] == 'GraphSidecar':  # mutiple image
        edges = getMutipleImage(message['code'])
        if not edges:
            return
        images = []
        for edge in edges:
            url = edge['node']['display_url']
            images.append({'url': url})
        m['extended_entities'] = images
        m['type'] = 'images'
    elif message['is_video']:
        m['type'] = 'video'
        video_url = getVideoUrl(m['href'])
        m['extended_entities'] = {
            'url': message['display_src'], 'video_url': video_url}
    else:
        m['type'] = 'image'

    i, insert = db_bz.updateOrInsert(
        Message, m, out_id=message['id'], m_type='instagram')
    if insert:
        print('%s new instagram %s' % (m['name'], m['out_id']))


def main():
    if len(sys.argv) == 3:
        god_name = (sys.argv[1])
        if sys.argv[2] == 'all':
            getAllMedia(god_name)
        exit(0)
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(sync, 'instagram', god_name)
        exit(0)
    while True:
        try:
            loop(sync, 'instagram')
        except CodeException as e:
            print(e)
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise  # Not error we are looking for
            print(e)
        except ConnectionError as e:
            print(e)
        except ValueError as e:
            print(e)
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1200)


if __name__ == '__main__':
    main()
    # import doctest
    # doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
