#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

import flask
from flask import Flask
from flask import request
from flask import jsonify
from flask_bz import ExtEncoder
import message
import oauth_bz


app = Flask(__name__)
app.json_encoder = ExtEncoder
app.secret_key = 'just test'


@app.route('/api_last')
def api_last():

    data = {
        'registered_count': oauth_bz.getCount()
    }

    return jsonify(data)


@app.route('/api_registered')
def api_registered():

    data = {
        'registered_count': oauth_bz.getCount()
    }

    return jsonify(data)


@app.route('/api_oauth_info')
def api_oauth_info():

    data = oauth_bz.getOauthInfo('5')
    return jsonify(data)


@app.route('/api_new')
def api_new():

    after = request.args.get('after', None)  # 晚于这个时间的
    limit = request.args.get('limit', 10)
    search_key = request.args.get('search_key', None)
    god_name = request.args.get('god_name', None)
    data = message.getNew(None, after, limit, search_key, god_name)
    return jsonify(data)


@app.route('/set')
def set():
    flask.session['user_id'] = '4'
    flask.session['bigzhu'] = 'very big'
    return 'kao'


@app.route('/get')
def get():
    return flask.session['user_id']


if __name__ == '__main__':
    app.debug = True
    app.run()
