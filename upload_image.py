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
    if result['status'] == 'error':
        print(url)
        print(result['error'])
        return 'error'
    else:
        return result["url"]


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
            print(url)
    session.commit()


if __name__ == '__main__':
    updateInstagram()
    #import doctest
    #doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
