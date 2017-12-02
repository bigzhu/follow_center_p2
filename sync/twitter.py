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
import db_bz
import datetime
import sys
import time
import tweepy
import exception_bz
from model import Message
import configparser
config = configparser.ConfigParser()
with open('./conf/twitter.ini', 'r') as cfg_file:
    config.readfp(cfg_file)
    consumer_key = config.get('secret', 'consumer_key')
    consumer_secret = config.get('secret', 'consumer_secret')
    access_token = config.get('secret', 'access_token')
    access_token_secret = config.get('secret', 'access_token_secret')
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
session = db_bz.session
from social_lib import loop


def needDel(error_info):
    '''
    出现这些报错, 说明没有 twitter 账户
    '''
    error_list = [
        'User not found.',
        'User has been suspended.'
        'Not authorized.',
        'Sorry, that page does not exist.'
    ]
    for i in error_list:
        if i in error_info:
            return True


def syncUserInfo(god_info):
    '''
    同步户信息
    >>> god_info = session.query(God).filter(God.name=='bigzhu').one()
    >>> syncUserInfo(god_info)
    True
    '''
    twitter_name = god_info.twitter['name']
    try:
        twitter_user = api.get_user(screen_name=twitter_name)
        # 不要用返回的name, 大小写会发生变化
        twitter = dict(
            type='twitter',
            name=twitter_name,
            count=twitter_user.followers_count,
            avatar=twitter_user.profile_image_url_https.replace(
                '_normal', '_400x400'),
            description=twitter_user.description
        )
        god_info.twitter = twitter
        return True
    except tweepy.error.TweepError:
        print('twitter_name=', twitter_name)
        error_info = exception_bz.getExpInfo()
        print(error_info)
        if needDel(error_info):
            god_info.twitter = {'name': ''}
            print('del %s twitter: %s' % (god_info.name, twitter_name))


def sync(god_info, wait):
    '''
    create by bigzhu at 15/07/04 22:49:04
        用 https://api.twitter.com/1.1/statuses/user_timeline.json 可以取到某个用户的信息
        参看 https://dev.twitter.com/rest/reference/get/statuses/user_timeline
    modify by bigzhu at 15/07/04 22:53:09
        考虑使用 http://www.tweepy.org/ 来调用twitter api
    modify by bigzhu at 15/08/02 21:35:46 避免批量微信通知
    create by bigzhu at 16/04/30 09:56:02 不再取转发的消息
    >>> god_info = session.query(God).filter(God.name=='bigzhu').one()
    >>> sync(god_info, None)
    '''
    god_name = god_info.name
    twitter_name = god_info.twitter['name']
    god_id = god_info.id
    try:
        if syncUserInfo(god_info) is None:
            return
        public_tweets = api.user_timeline(
            screen_name=twitter_name, include_rts=False, exclude_replies=True)
        for tweet in public_tweets:
            # print(tweet.created_at.tzname())
            # tweet.created_at += timedelta(hours=8)
            saveMessage(god_name, twitter_name, god_id, tweet)
        # oper.noMessageTooLong('twitter', user.twitter)
    except tweepy.error.TweepError:
        print('twitter_name=', twitter_name)
        error_info = exception_bz.getExpInfo()
        print(error_info)
        if needDel(error_info):
            god_info.twitter = {'name': ''}

        if 'Rate limit exceeded' in error_info or 'Max retries exceeded with url' in error_info:  # 调用太多
            if wait:
                waitReset(god_info)
            else:
                raise Exception('Twitter api 的调用次数用完了，请等个10分钟再添加!')
            return 'Rate limit exceeded'


def saveMessage(god_name, twitter_name, god_id, tweet):
    '''
    create by bigzhu at 15/07/10 14:39:48
        保存twitter
    create by bigzhu at 16/03/26 06:05:12 重构，改很多
    modify by bigzhu at 16/03/26 20:33:59 重构
        user 本系统用户信息
        tweet 消息本身
    modify by bigzhu at 17/01/13 15:38:11 去了用不到的
    '''
    m = dict(
        god_id=god_id,
        god_name=god_name,
        name=twitter_name,
        out_id=tweet.id_str,
        m_type='twitter',
        created_at=tweet.created_at,
        content=None,
        text=tweet.text
    )
    if hasattr(tweet, 'extended_entities'):
        m['extended_entities'] = tweet.extended_entities
        m['type'] = tweet.extended_entities['media'][0]['type']
    m['href'] = 'https://twitter.com/' + \
        twitter_name + '/status/' + tweet.id_str
    i, insert = db_bz.updateOrInsert(
        Message, m, out_id=tweet.id_str, m_type='twitter')
    if insert:
        print('%s new twitter %s' % (m['name'], m['out_id']))
    return id


def getRemaining():
    '''
    create by bigzhu at 16/04/30 10:31:58 取重置时间和剩余调用次数
    '''
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    rs = api.rate_limit_status()
    con = rs['resources']
    # reset = con['statuses']['/statuses/user_timeline']['reset']
    remaining = con['statuses']['/statuses/user_timeline']['remaining']
    return remaining


def waitReset(god_info):
    while True:
        try:
            remaining = getRemaining()
        except tweepy.error.TweepError:
            error_info = exception_bz.getExpInfo()
            print(error_info)
            time.sleep(1200)
            continue
        print('remaining:', remaining)
        if remaining == 0:
            time.sleep(1200)
        else:
            sync(god_info, wait=True)
            break


def main():
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(sync, 'twitter', god_name)
        exit(0)

    while True:
        loop(sync, 'twitter', wait=True)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(2400)


if __name__ == '__main__':
    main()
    #import doctest
    #doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
