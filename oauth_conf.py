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


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
