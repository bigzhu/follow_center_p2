#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")


from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect
from flask_bz import ExtEncoder
from flask import session as cookie
import message_oper
import oauth_bz
import conf
import last_oper
import cat_oper
import god_oper
import anki_oper
from db_bz import session

import db_bz
import model


app = Flask(__name__)
app.json_encoder = ExtEncoder
app.secret_key = conf.cookie_secret
# js 需要访问 cookies
app.config['SESSION_COOKIE_HTTPONLY'] = False


@app.route('/api_no_types', methods=['GET', 'PUT'])
def api_no_types():

    data = '0'
    user_id = cookie['user_id']
    if request.method == 'PUT':
        no_types = request.get_json()
        if no_types:
            data = dict(user_id=user_id, no_types=no_types)
            db_bz.updateOrInsert(model.MessageConf, data, user_id=user_id)
            session.commit()
    elif request.method == 'GET':
        no_types = db_bz.session.query(model.MessageConf.no_types).filter(
            model.MessageConf.user_id == user_id).one_or_none()
        if no_types:
            data = no_types._asdict()['no_types']
        else:
            data = []

    return jsonify(data)


@app.route('/api_anki', methods=['POST'])
def api_anki():
    data = request.get_json()
    front = data['front']
    user_id = cookie['user_id']
    message_id = data['message_id']
    anki_oper.addCard(front, user_id)
    anki_oper.saveAnki(message_id, user_id)
    session.commit()
    return jsonify("0")


@app.route('/api_logout')
def api_logout():
    cookie.pop('user_id')
    # return jsonify("0")
    return redirect('/', code=302)


@app.route('/api_login', methods=['POST'])
def api_login():

    data = request.get_json()
    user_name = data['user_name']
    # password = data['password']
    oauth_info = oauth_bz.getOauthInfo(None, user_name, 'github')

    cookie.permanent = True
    cookie['user_id'] = str(oauth_info.id)

    return jsonify("0")


@app.route('/api_old')
def api_old():
    before = request.args.get('before')
    god_name = request.args.get('god_name')
    search_key = request.args.get('search_key')
    limit = request.args.get('limit', 10)
    user_id = cookie.get('user_id')
    data = message_oper.getOld(user_id, before, limit, search_key, god_name)
    return jsonify(data)


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
    session.commit()

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
    if user_id is None:
        return jsonify({'name': ''})
    data = oauth_bz.getOauthInfo(user_id)
    return jsonify(data)


@app.route('/api_new')
def api_new():

    after = request.args.get('after', None)  # 晚于这个时间的
    not_types = request.args.getlist('not[]')
    limit = request.args.get('limit', 10)
    search_key = request.args.get('search_key', None)
    god_name = request.args.get('god_name', None)
    data = message_oper.getNew(cookie.get('user_id'), after,
                               limit, search_key, god_name, not_types)
    return jsonify(data)


@app.teardown_request
def shutdown_session(exception=None):
    session.remove()


@app.errorhandler(Exception)
def all_exception_handler(error):
    return 'Error', 500


if __name__ == '__main__':
    app.debug = True
    app.run()
