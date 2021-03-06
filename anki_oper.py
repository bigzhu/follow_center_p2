#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import requests
import json
import db_bz
import html_bz
import model

import re
from bs4 import BeautifulSoup
DECK = 'Default'
URL = 'https://ankiweb.net/account/login'
client = None
cookies = None
from model import AnkiSave
from db_bz import session


def saveAnki(message_id, user_id):
    '''
    记录哪些 message 已提到 anki 了
    '''
    anki_save = locals()

    db_bz.getOrInsert(AnkiSave, anki_save,
                      message_id=message_id, user_id=user_id)


def getAnkiConfig(user_id):
    '''
    查出anki记录
    >>> getAnkiConfig('1')
    <model.Anki object at...
    '''
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
    soup = BeautifulSoup(r.text, 'html.parser')

    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')
    return csrf_token


def login(username, password):
    global client
    global cookies
    csrf_token = getLoginCsrfToken()
    login_info = {'submitted': '1', 'csrf_token': str(
        csrf_token), 'username': username, 'password': password}
    r = client.post(URL, data=login_info, cookies=cookies)
    if 'the password you provided does not match our records' in r.text:
        raise Exception('密码不正确')
    # cookies = r.cookies
    cookies = client.cookies


def getMidAndCsrfTokenHolder(user_id, reset_cookie=False):
    data = getAnkiConfig(user_id)
    if data.mid is not None and not reset_cookie:
        return data.mid, data.csrf_token, data.cookie
    mid, csrf_token, cookie = getMidAndCsrfToken(data.user_name, data.password)
    anki_info = session.query(model.Anki).filter(
        model.Anki.user_id == user_id).first()
    anki_info.mid = mid
    anki_info.csrf_token = csrf_token
    anki_info.cookie = cookie
    session.commit()
    session.close()
    return mid, csrf_token, cookie


def getMidAndCsrfToken(user_name, password):
    '''
    添加时要取得一个mide参数,在登录后的页面有
    '''
    global client
    global cookies
    login(user_name, password)
    edit_url = 'https://ankiuser.net/edit/'
    r = client.get(edit_url, cookies=cookies)

    mid = re.findall(r'editor.curModelID = "\d+"', r.text)
    if len(mid) == 0:
        raise Exception('找不到mid')
    mid = mid[0].replace('editor.curModelID = "', '').replace('"', '')

    csrf_token = re.findall(r"editor.csrf_token2 = '\S+'", r.text)[0]
    csrf_token = csrf_token.replace(
        "editor.csrf_token2 = '", '').replace("'", '')
    # r 里拿不到 cookies 了, 只有从 session 里拿
    cookies = client.cookies
    cookie = cookies.get('ankiweb', domain='ankiuser.net')
    return mid, csrf_token, cookie


def getStrCookie(cookies):
    return 'ankiweb=%s' % cookies['ankiweb']


def addCard(front, user_id, not_try=None):
    '''
    not_try: true 不再因403而再次调
    >>> addCard('test', '4', True)
    '''
    mid, csrf_token, cookie = getMidAndCsrfTokenHolder(user_id)

    front = html_bz.relativePathToAbsolute(front, 'https://follow.center')
    data = [[front, ''], '']
    data = json.dumps(data)
    cookies = {'ankiweb': cookie}
    save_info = {'data': data, 'mid': str(
        mid), 'deck': DECK, 'csrf_token': str(csrf_token)}
    # r = requests.post('https://ankiuser.net/edit/save',
    r = requests.post('https://ankiuser.net/edit/save',
                      cookies=cookies, data=save_info)
    if r.text != '1':
        if '403 Forbidden' in r.text and not_try is None:
            getMidAndCsrfTokenHolder(user_id, True)
            addCard(front, user_id, True)
        else:
            raise Exception('error: %s' % r.text)


if __name__ == '__main__':
    # getMidAndCsrfTokenHolder('4', True)
    addCard('test_fuck5', '4')
    # import doctest
    # doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
