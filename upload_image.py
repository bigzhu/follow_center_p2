#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import message_oper
import db_bz
session = db_bz.session


def uploadImgByURL(url):
    '''
    根据url上传图片到postimages中
    '''
    headers = {'User-Agent': 'Mozilla/5.0'}
    payload = {'url': url,
               'numfiles': 1,
               'upload_session': 'IfoAM1UCrRamfYXhVak854ywR5kbLsXs',
               'token': '61aa06d6116f7331ad7b2ba9c7fb707ec9b182e8'
               }

    session = requests.Session()
    r = session.post('https://postimages.org/json/rr',
                     headers=headers, data=payload)
    result = r.json()
    if result.get('status') == 'OK':
        return result["url"]
    else:
        print(result.get('status'))
        return 'error'


def getOrginImgURL(url):
    '''
    从返回的 url 地址中获取原图地址
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    a = soup.find('a', id='download')
    return a['href']


def main(url):
    url = uploadImgByURL(url)
    if url == 'error':
        return url
    # 剔除最后一个 path
    url = url.rpartition('/')[0]
    url = url.rpartition('/')[0]
    return getOrginImgURL(url)


def updateInstagram():
    ins = message_oper.getNotUploadImageMessagesByMType('instagram')
    for i in ins:
        if i.type == 'image':
            url = i.extended_entities['url']
            url = main(url)
            i.images = [url]
            session.commit()
            print(url)
        if i.type == 'images':
            i.images = []
            for v in i.extended_entities:
                url = main(v['url'])
                # 其中一个出错, 其他也不用试了
                if url == "error":
                    i.images = [url]
                    break
                else:
                    i.images.append(url)
            print(i.images)
            session.commit()


def updateTwitter():
    ins = message_oper.getNotUploadImageMessagesByMType('twitter')
    for i in ins:
        if i.type == 'photo':
            i.images = []
            for v in i.extended_entities['media']:
                print(v)
                url = v['media_url_https'] + ':orig'
                url = main(v['url'])
                # 其中一个出错, 其他也不用试了
                if url == "error":
                    i.images = [url]
                    break
                else:
                    i.images.append(url)
            print(i.images)
            session.commit()


if __name__ == '__main__':
    updateTwitter()
    #import doctest
    #doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
