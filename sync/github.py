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
import sys
import god_oper
import db_bz
import time_bz
from model import Message
import time
import exception_bz
from sync.social_lib import loop

import configparser
config = configparser.ConfigParser()
with open('conf/github.ini', 'r') as cfg_file:
    config.readfp(cfg_file)
    client_id = config.get('secret', 'client_id')
    client_secret = config.get('secret', 'client_secret')
params = {'client_id': client_id, 'client_secret': client_secret}


def getGithubUser(github_name, god_name):
    try:
        r = requests.get('https://api.github.com/users/%s' %
                         github_name, params=params)
        github_user = r.json()
        message = github_user.get('message')
        if message == 'Not Found':
            god_oper.delNoName('github', god_name)
            return
        return github_user
    except requests.exceptions.ConnectionError:
        print(exception_bz.getExpInfoAll())
        return
    except ValueError:
        print(exception_bz.getExpInfoAll())
        return


def sync(god, wait):
    '''
    create by bigzhu at 15/07/15 17:54:08 取github
    modify by bigzhu at 15/07/22 16:20:42 时间同样要加入8小时,否则不正确
    '''
    github_name = god.github['name']
    god_name = god.name
    god_id = god.id

    etag = god.github.get('sync_key')
    github_user = getGithubUser(github_name, god_name)
    if github_user is None:
        return
    headers = {'If-None-Match': etag}
    try:
        r = requests.get('https://api.github.com/users/%s/events' %
                         github_name, headers=headers, params=params)
    except requests.exceptions.ConnectionError:
        print(exception_bz.getExpInfoAll())
        return
    if r.status_code == 200:
        etag = r.headers['etag']
        limit = r.headers['X-RateLimit-Remaining']
        if limit == '0':
            return
        for message in r.json():
            saveMessage(god_name, github_name, god_id, message)
        # oper.noMessageTooLong('github', github_name)
        saveUser(god, github_user, etag)  # 为了update etag
    if r.status_code == 404:
        # public_db.sendDelApply('github', god_name, github_name, '404')
        god_oper.delNoName('github', god_name)


def saveMessage(god_name, github_name, god_id, message):
    '''
    create by bigzhu at 15/07/16 09:44:39 为了抽取数据方便,合并数据到 content 里
    '''
    content = dict(
        type=message['type'],
        repo=message['repo'],
        payload=message['payload']
    )

    m = dict(
        god_id=god_id,
        god_name=god_name,
        name=github_name,
        out_id=message['id'],
        m_type='github',
        out_created_at=time_bz.jsonToDatetime(message['created_at']),
        # m.created_at += timedelta(hours=8)
        content=content,
        text=None,
        href=None,
    )
    i, insert = db_bz.updateOrInsert(
        Message, m, out_id=message['id'], m_type='github')
    if insert:
        print('%s new github %s' % (m['name'], m['out_id']))
    return id


def saveUser(god, user, sync_key=None):
    github = dict(
        type='github',
        name=god.github['name'],
        avatar=user.get('avatar_url', ''),
        description=user.get('bio'),
        id=user['id'],
        sync_key=sync_key
    )
    if user.get('followers') is None:
        github['count'] = -1
    else:
        github['count'] = user['followers']
    if sync_key is not None:
        github['sync_key'] = sync_key

    god.github = github
    return True


def main():
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(sync, 'github', god_name)
        exit(0)
    while True:
        loop(sync, 'github', wait=True)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1200)


if __name__ == '__main__':
    main()
