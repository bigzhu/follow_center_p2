#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")


from flask import Flask
from flask import request
from flask import jsonify
from flask_bz import ExtEncoder
from flask import session as cookie
import message_oper
import oauth_bz
import conf
import last_oper
import cat_oper
import god as god_oper


app = Flask(__name__)
app.json_encoder = ExtEncoder
app.secret_key = conf.cookie_secret


@app.route('/api_god')
def api_god():
    god_name = request.args.get('god_name', None)
    user_id = cookie.get('user_id')
    data = god_oper.getGod(god_name, user_id)
    if data is None:
        raise Exception('不存在 %s' % god_name)
    return jsonify(data)


@app.route('/api_gods')
def api_gods():
    """
    @apiGroup god
    @api {get} /api_gods 推荐关注的人
    @apiParam {String} cat 分类
    @apiParam {String} before 早于这个时间的(取更多)
    @apiParam {Number} limit 一次取几个
    @apiParam {Boolean} followed 已关注, 否则为推荐
    """
    cat = request.args.get('cat', None)
    before = request.args.get('before', None)
    limit = request.args.get('limit', 6)
    followed = request.args.get('followed', False)
    user_id = cookie.get('user_id')

    data = god_oper.getGods(user_id, cat, before, limit, followed)

    return jsonify(data)


@app.route('/api_cat')
def api_cat():

    user_id = cookie.get('user_id')
    followed = request.args.get('is_my', None)
    data = cat_oper.getCat(user_id, followed)

    return jsonify(data)


@app.route('/api_last', methods=['PUT'])
def api_last():

    user_id = cookie.get('user_id')
    if user_id is None:
        return jsonify('0')

    last = request.get_json().get('last')
    last_oper.saveLast(user_id, last)

    unread_message_count = message_oper.getUnreadCount(user_id, last)
    return jsonify(unread_message_count)


@app.route('/api_registered')
def api_registered():

    data = {
        'registered_count': oauth_bz.getCount()
    }

    return jsonify(data)


@app.route('/api_oauth_info')
def api_oauth_info():

    user_id = cookie.get('user_id')
    data = oauth_bz.getOauthInfo(user_id)
    return jsonify(data)


@app.route('/api_new')
def api_new():

    after = request.args.get('after', None)  # 晚于这个时间的
    limit = request.args.get('limit', 10)
    search_key = request.args.get('search_key', None)
    god_name = request.args.get('god_name', None)
    data = message_oper.getNew(cookie.get('user_id'), after,
                          limit, search_key, god_name)
    return jsonify(data)


@app.route('/set')
def set():

    cookie['user_id'] = '4'
    return jsonify("done")


if __name__ == '__main__':
    app.debug = True
    app.run()
