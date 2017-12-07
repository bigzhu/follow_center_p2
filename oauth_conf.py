#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_oauthlib.client import OAuth

import configparser
config = configparser.ConfigParser()


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
