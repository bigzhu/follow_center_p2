#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_oauthlib.client import OAuth

import configparser
import json
config = configparser.ConfigParser()

from flask import session


def update_qq_api_request_data(data={}):
    '''Update some required parameters for OAuth2.0 API calls'''
    with open('conf/qq.ini', 'r') as cfg_file:
        config.readfp(cfg_file)
        consumer_key = config.get('secret', 'consumer_key')
    defaults = {
        'openid': session.get('qq_openid'),
        'access_token': session.get('qq_token')[0],
        'oauth_consumer_key': consumer_key,
    }
    defaults.update(data)
    return defaults


def json_to_dict(x):
    '''OAuthResponse class can't parse the JSON data with content-type
-    text/html and because of a rubbish api, we can't just tell flask-oauthlib to treat it as json.'''
    if x.find(b'callback') > -1:
        # the rubbish api (https://graph.qq.com/oauth2.0/authorize) is handled here as special case
        pos_lb = x.find(b'{')
        pos_rb = x.find(b'}')
        x = x[pos_lb:pos_rb + 1]

    try:
        if type(x) != str:  # Py3k
            x = x.decode('utf-8')
        return json.loads(x, encoding='utf-8')
    except:
        return x


def getQQ(app):
    oauth = OAuth(app)
    with open('conf/qq.ini', 'r') as cfg_file:
        config.readfp(cfg_file)
        consumer_key = config.get('secret', 'consumer_key')
        consumer_secret = config.get('secret', 'consumer_secret')

    qq = oauth.remote_app(
        'qq',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        base_url='https://graph.qq.com',
        request_token_url=None,
        request_token_params={'scope': 'get_user_info'},
        access_token_url='/oauth2.0/token',
        authorize_url='/oauth2.0/authorize',
    )
    return qq


def getTwitter(app):
    oauth = OAuth(app)
    with open('conf/twitter.ini', 'r') as cfg_file:
        config.readfp(cfg_file)
        consumer_key = config.get('secret', 'consumer_key')
        consumer_secret = config.get('secret', 'consumer_secret')
        #access_token = config.get('secret', 'access_token')
        #access_token_secret = config.get('secret', 'access_token_secret')

    twitter = oauth.remote_app(
        'twitter',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        base_url='https://api.twitter.com/1.1/',
        request_token_url='https://api.twitter.com/oauth/request_token',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authorize'
    )
    return twitter


def getGithub(app):
    with open('conf/github.ini', 'r') as cfg_file:
        config.readfp(cfg_file)
        consumer_key = config.get('secret', 'consumer_key')
        consumer_secret = config.get('secret', 'consumer_secret')
    oauth = OAuth(app)
    github = oauth.remote_app(
        'github',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        request_token_params={'scope': 'user:email'},
        base_url='https://api.github.com/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize'
    )
    return github


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
