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

import datetime
import sys
import time
import god_oper
from datetime import timedelta
import tweepy
from db_bz import pg
import json
import public_bz
import social_sync
import ConfigParser
config = ConfigParser.ConfigParser()
with open('../conf/twitter.ini', 'r') as cfg_file:
    config.readfp(cfg_file)
    consumer_key = config.get('secret', 'consumer_key')
    consumer_secret = config.get('secret', 'consumer_secret')
    access_token = config.get('secret', 'access_token')
    access_token_secret = config.get('secret', 'access_token_secret')
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def getTwitterUser(twitter_name, god_name):
    twitter_user = None
    try:
        twitter_user = api.get_user(screen_name=twitter_name)
    except tweepy.error.TweepError:
        print 'twitter_name=', twitter_name
        error_info = public_bz.getExpInfo()
        print error_info

        if 'User not found.' in error_info:
            god_oper.delNoName('twitter', god_name)
        if 'User has been suspended.' in error_info:  # 帐号被冻结了
            god_oper.delNoName('twitter', god_name)
        if 'Not authorized.' in error_info:  # 私有
            god_oper.delNoName('twitter', god_name)
        if 'Sorry, that page does not exist.' in error_info:  # 没用户
            god_oper.delNoName('twitter', god_name)
    if twitter_user:
        twitter_user = saveUser(god_name, twitter_name, twitter_user)
    else:
        god_oper.delNoName('twitter', god_name)
    return twitter_user


def saveUser(god_name, twitter_name, twitter_user):
    social_user = public_bz.storage()
    # 不要用返回的name, 大小写会发生变化
    # social_user.name = twitter_user.screen_name
    social_user.name = twitter_name
    social_user.type = 'twitter'
    social_user.count = twitter_user.followers_count
    social_user.avatar = twitter_user.profile_image_url_https.replace('_normal', '_400x400')
    social_user.description = twitter_user.description
    # 没有找到
    # social_user.sync_key = twitter_user.description

    pg.update('god', where={'name': god_name}, twitter=json.dumps(social_user))
    return social_user


def main(god, wait):
    '''
    create by bigzhu at 15/07/04 22:49:04
        用 https://api.twitter.com/1.1/statuses/user_timeline.json 可以取到某个用户的信息
        参看 https://dev.twitter.com/rest/reference/get/statuses/user_timeline
    modify by bigzhu at 15/07/04 22:53:09
        考虑使用 http://www.tweepy.org/ 来调用twitter api
    modify by bigzhu at 15/08/02 21:35:46 避免批量微信通知
    create by bigzhu at 16/04/30 09:56:02 不再取转发的消息
    '''
    god_name = god.name
    twitter_name = god.twitter['name']
    god_id = god.id
    try:
        twitter_user = getTwitterUser(twitter_name, god_name)
        if not twitter_user:
            return
        public_tweets = api.user_timeline(screen_name=twitter_name, include_rts=False, exclude_replies=True)
        for tweet in public_tweets:
            tweet.created_at += timedelta(hours=8)
            saveMessage(god_name, twitter_name, god_id, tweet)
        # oper.noMessageTooLong('twitter', user.twitter)
    except tweepy.error.TweepError:
        print 'twitter_name=', twitter_name
        error_info = public_bz.getExpInfo()
        print error_info

        if 'User not found.' in error_info:
            god_oper.delNoName('twitter', god_name)
        if 'Rate limit exceeded' in error_info:  # 调用太多
            if wait:
                waitReset(god_name, twitter_name, god_id)
            else:
                raise Exception('Twitter api 的调用次数用完了，请等个10分钟再添加!')
            return 'Rate limit exceeded'
        if 'User has been suspended.' in error_info:  # 帐号被冻结了
            god_oper.delNoName('twitter', god_name)
        if 'Not authorized.' in error_info:  # 私有
            god_oper.delNoName('twitter', god_name)
        if 'Sorry, that page does not exist.' in error_info:  # 没用户
            god_oper.delNoName('twitter', god_name)


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
    m = public_bz.storage()
    m.god_id = god_id
    m.god_name = god_name
    m.name = twitter_name

    m.id_str = tweet.id_str
    m.m_type = 'twitter'
    m.created_at = tweet.created_at
    m.content = None
    m.text = tweet.text
    if hasattr(tweet, 'extended_entities'):
        m.extended_entities = json.dumps(tweet.extended_entities)
        m.type = tweet.extended_entities['media'][0]['type']
    m.href = 'https://twitter.com/' + m.name + '/status/' + m.id_str
    id = pg.insertIfNotExist('message', m, "id_str='%s' and m_type='twitter'" % tweet.id_str)
    if id is not None:
        print '%s new twitter %s' % (m.name, m.id_str)
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


def waitReset(god_name, twitter_name, god_id):
    while True:
        try:
            remaining = getRemaining()
        except tweepy.error.TweepError:
            error_info = public_bz.getExpInfo()
            print error_info
            time.sleep(1200)
            continue
        print 'remaining:', remaining
        if remaining == 0:
            time.sleep(1200)
        else:
            main(god_name, twitter_name, god_id, wait=True)
            break


def loop(god_name=None, wait=None):
    '''
    create by bigzhu at 16/05/30 13:26:38 取出所有的gods，同步
    '''
    gods = social_sync.getSocialGods('twitter', god_name)
    for god in gods:
        main(god, wait)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        god_name = (sys.argv[1])
        loop(god_name)
        exit(0)

    while True:
        loop(wait=True)
        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(2400)
