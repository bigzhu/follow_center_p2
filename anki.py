#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import requests
import json
import db_bz
import model

import re
from bs4 import BeautifulSoup
DECK = 'Default'
URL = 'https://ankiweb.net/account/login'
client = None
cookies = None


def getAnkiConfig(user_id):
    '''
    查出anki记录
    >>> getAnkiConfig('1')
    <model.Anki object at...
    '''
    session = db_bz.getSession()
    datas = session.query(model.Anki).filter_by(user_id=user_id).all()
    if(len(datas) == 0):
        raise Exception('你还没有配置Anki信息')
    return datas[0]


def getLoginCsrfToken():
    '''
    登录页的 csrf_token
    '''

    global client
    global cookies
    client = requests.session()
    r = client.get(URL)
    cookies = r.cookies
    soup = BeautifulSoup(r.text)

    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')
    return csrf_token


def login(username, password):
    global client
    global cookies
    csrf_token = getLoginCsrfToken()
    login_info = {'submitted': '1', 'csrf_token': str(csrf_token), 'username': username, 'password': password}
    print(login_info)
    r = client.post(URL, data=login_info, cookies=cookies)
    if 'the password you provided does not match our records' in r.text:
        raise Exception('密码不正确')
    cookies = r.cookies


def getMidAndCsrfTokenHolder(user_id, reset_cookie=False):
    data = getAnkiConfig(user_id)
    if data.mid is not None and not reset_cookie:
        return data.mid, data.csrf_token, data.cookie
    mid, csrf_token, cookie = getMidAndCsrfToken(data.user_name, data.password)
    sql = '''
    update anki set mid='%s', csrf_token='%s', cookie='%s' where user_id='%s'
    ''' % (mid, csrf_token, cookie, user_id)
    pg.query(sql)
    return mid, csrf_token, cookie


def getMidAndCsrfToken(user_name, password):
    '''
    添加时要取得一个mide参数,在登录后的页面有
    '''
    global client
    global cookies
    login(user_name, password)
    edit_url = 'https://ankiweb.net/edit/'
    r = client.get(edit_url, cookies=cookies)

    mid = re.findall(r'editor.curModelID = "\d+"', r.text)
    if len(mid) == 0:
        raise Exception('找不到mid')
    mid = mid[0].replace('editor.curModelID = "', '').replace('"', '')

    # mid = re.findall(r'"mid": \d+', r.text)
    # if len(mid) == 0:
    #     mid = re.findall(r'"mid": "\d+"', r.text)
    #     if len(mid) == 0:
    #         print r.text
    #         raise Exception('找不到mid')
    # mid = mid[0]
    # mid = mid.replace('"mid": ', '')
    # mid = mid.replace('"', '')

    csrf_token = re.findall(r"editor.csrf_token2 = '\S+'", r.text)[0]
    csrf_token = csrf_token.replace("editor.csrf_token2 = '", '').replace("'", '')
    cookies = r.cookies
    cookie = cookies['ankiweb']
    return mid, csrf_token, cookie


def getStrCookie(cookies):
    return 'ankiweb=%s' % cookies['ankiweb']


def addCard(front, user_id, not_try=None):
    '''
    not_try: true 不再因403而再次调
    '''
    mid, csrf_token, cookie = getMidAndCsrfTokenHolder(user_id)

    front = oper_bz.relativePathToAbsolute(front, 'https://follow.center')
    data = [[front, ''], '']
    data = json.dumps(data)
    cookies = {'ankiweb': cookie}
    save_info = {'data': data, 'mid': str(mid), 'deck': DECK, 'csrf_token': str(csrf_token)}
    r = requests.post('https://ankiweb.net/edit/save', cookies=cookies, data=save_info)
    if r.text != '1':
        if '403 Forbidden' in r.text and not_try is None:
            getMidAndCsrfTokenHolder(user_id, True)
            addCard(front, user_id, True)
        else:
            raise Exception('error: %s' % r.text)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
