#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
create by bigzhu at 15/07/15 17:17:29 取github的动态
'''
import sys
sys.path.append("../../lib_py")

import datetime
import requests
from db_bz import pg
import sys
from datetime import timedelta
from public_bz import storage
import god_oper
import json
import time_bz
import time
import public_bz
import social_sync

import ConfigParser
config = ConfigParser.ConfigParser()
with open('conf/github.ini', 'r') as cfg_file:
    config.readfp(cfg_file)
    client_id = config.get('secret', 'client_id')
    client_secret = config.get('secret', 'client_secret')
params = {'client_id': client_id, 'client_secret': client_secret}


def getGithubUser(github_name, god_name):
    try:
        r = requests.get('https://api.github.com/users/%s' % github_name, params=params)
        github_user = r.json()
        message = github_user.get('message')
        if message == 'Not Found':
            god_oper.delNoName('github', god_name)
            return
        saveUser(god_name, github_name, github_user)
        return github_user
    except requests.exceptions.ConnectionError:
        print(public_bz.getExpInfoAll())
        return
    except ValueError:
        print(public_bz.getExpInfoAll())
        return


def main(god, wait):
    '''
    create by bigzhu at 15/07/15 17:54:08 取github
    modify by bigzhu at 15/07/22 16:20:42 时间同样要加入8小时,否则不正确
    '''
    god_name = god.name
    github_name = god.github['name']
    god_id = god.id

    etag = god.github.get('sync_key')
    github_user = getGithubUser(github_name, god_name)
    if github_user is None:
        return
    headers = {'If-None-Match': etag}
    try:
        r = requests.get('https://api.github.com/users/%s/events' % github_name, headers=headers, params=params)
    except requests.exceptions.ConnectionError:
        print(public_bz.getExpInfoAll())
        return
    if r.status_code == 200:
        etag = r.headers['etag']
        limit = r.headers['X-RateLimit-Remaining']
        if limit == '0':
            return
        for message in r.json():
            message = storage(message)
            saveMessage(god_name, github_name, god_id, message)
        # oper.noMessageTooLong('github', github_name)
        saveUser(god_name, github_name, github_user, etag)  # 为了update etag
    if r.status_code == 404:
        # public_db.sendDelApply('github', god_name, github_name, '404')
        god_oper.delNoName('github', god_name)


def saveMessage(god_name, github_name, god_id, message):
    '''
    create by bigzhu at 15/07/16 09:44:39 为了抽取数据方便,合并数据到 content 里
    '''
    content = storage()
    content.type = message.type
    content.repo = message.repo
    content.payload = message.payload
    content = json.dumps(content)

    m = public_bz.storage()
    m.god_id = god_id
    m.god_name = god_name
    m.name = github_name
    # m.avatar = message.actor['avatar_url']

    m.id_str = message['id']
    m.m_type = 'github'
    m.created_at = time_bz.unicodeToDateTIme(message.created_at)
    m.created_at += timedelta(hours=8)
    m.content = content
    m.text = None
    m.href = None
    id = pg.insertIfNotExist('message', m, "id_str='%s' and m_type='github'" % m.id_str)
    if id is not None:
        print('%s new github %s' % (m.name, m.id_str))
    return id


def saveUser(god_name, github_name, user, sync_key=None):
    social_user = public_bz.storage()

    try:
        # social_user.name = user['login']
        social_user.name = github_name
    except Exception as e:
        print(e)
        print(user)
    social_user.type = 'github'
    if user.get('followers') is None:
        social_user.count = -1
    else:
        social_user.count = user['followers']
    social_user.avatar = user.get('avatar_url', '')
    social_user.description = user.get('bio')
    if sync_key is not None:
        social_user.sync_key = sync_key

    pg.update('god', where={'name': god_name}, github=json.dumps(social_user))
    return social_user


def loop(god_name=None, wait=None):
    '''
    '''
    gods = social_sync.getSocialGods('github', god_name)
    for god in gods:
        main(god, wait)


if __name__ == '__main__':
    # print json.dumps(getGithubUser('kdzwinel', 'kdzwinel'))
    if len(sys.argv) == 2:
        user_name = (sys.argv[1])
        loop(user_name)
        exit(0)
    while True:
        loop(wait=True)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1200)
