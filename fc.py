#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")


from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask import flash

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

from model import God
import db_bz
import model
import url_bz
import follow_who_oper
from sync import twitter
from sync import instagram
from sync import tumblr
from sync import github
# from sync import github
# import exception_bz
import collect_oper
from flask_oauthlib.client import OAuth
import oauth_conf


app = Flask(__name__)
app.json_encoder = ExtEncoder
app.secret_key = conf.cookie_secret
# js 需要访问 cookies
app.config['SESSION_COOKIE_HTTPONLY'] = False
oauth = OAuth(app)

twitter = oauth_conf.getTwitter(app)
github = oauth_conf.getGithub(app)


@github.tokengetter
def get_github_oauth_token():
    return cookie.get('github_token')


@app.route('/api_github_oauthorized')
def api_github_oauthorized():
    resp = github.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason=%s error=%s resp=%s' % (
            request.args['error'],
            request.args['error_description'],
            resp
        )
    print(resp['access_token'])
    cookie['github_token'] = (resp['access_token'], '')
    me = github.get('user')
    user = me.data
    oauth_info = dict(
        out_id=user['id'],
        type='github',
        name=user['login'],
        avatar=user['avatar_url'],
        email=user['email'],
        location=user['location']
    )

    oauth_info, is_insert = oauth_bz.saveAndGetOauth(oauth_info)
    cookie['user_id'] = str(oauth_info.id)
    return redirect('/')


@app.route('/api_github')
def api_github():
    return github.authorize(callback=url_for('api_github_oauthorized', _external=True))


@twitter.tokengetter
def get_twitter_token():
    if 'twitter_oauth' in cookie:
        resp = cookie['twitter_oauth']
        return resp['oauth_token'], resp['oauth_token_secret']


@app.route('/api_twitter')
def api_twitter():
    callback_url = url_for('api_twitter_oauthorized',
                           next=request.args.get('next'), _external=True)
    return twitter.authorize(callback=callback_url or request.referrer or None)


@app.route('/api_twitter_oauthorized')
def api_twitter_oauthorized():
    resp = twitter.authorized_response()

    if resp is None:
        flash('You denied the request to sign in.')
    else:
        cookie['twitter_oauth'] = resp
        resp = twitter.request('account/verify_credentials.json')
        if resp.status == 200:
            user = resp.data
        else:
            flash('Unable to load user info from Twitter.')

        oauth_info = dict(
            out_id=user['id'],
            type='twitter',
            name=user['name'],
            avatar=user['profile_image_url_https'],
            location=user['location']
        )

        oauth_info, is_insert = oauth_bz.saveAndGetOauth(oauth_info)
        cookie['user_id'] = str(oauth_info.id)

    return redirect('/')


@app.route('/api_follow', methods=['POST', 'DELETE'])
def api_follow():
    user_id = cookie['user_id']
    if request.method == 'POST':
        data = request.get_json()
        god_id = data['god_id']
        follow_who_oper.follow(user_id, god_id)
        session.commit()
        return jsonify('0')
    elif request.method == 'DELETE':
        god_id = request.args['god_id']
        follow_who_oper.unFollow(user_id, god_id)
        session.commit()
        return jsonify('0')


@app.route('/api_collect', methods=['GET', 'POST', 'DELETE'])
def api_collect():
    user_id = cookie['user_id']
    if request.method == 'POST':
        data = request.get_json()
        message_id = data['message_id']
        collect_oper.collect(message_id, user_id)
        session.commit()
        return jsonify('0')
    elif request.method == 'GET':
        data = collect_oper.getCollect(user_id)
        return jsonify(data)
    elif request.method == 'DELETE':
        message_id = request.args['message_id']
        collect_oper.deleteCollect(message_id, user_id)
        session.commit()
        return jsonify('0')


@app.route('/api_remark', methods=['POST'])
def api_remark():
    data = request.get_json()
    god_id = data['god_id']
    remark = data['remark']
    user_id = cookie['user_id']
    remark = dict(
        user_id=user_id,
        remark=remark,
        god_id=god_id
    )
    db_bz.updateOrInsert(model.Remark, remark, user_id=user_id, god_id=god_id)
    session.commit()
    return jsonify('0')


@app.route('/api_social')
def api_social():
    name = request.args.get('name')
    type = request.args.get('type')
    # user_id = cookie['user_id']
    god = session.query(God).filter(God.name.ilike(name)).one_or_none()
    if god is None:
        raise Exception('没有正确加入 god %s' % name)

    social = getattr(god, type)
    if social.get('count'):
        data = social
    else:
        if type == 'twitter':
            twitter.sync(god, False)
            data = getattr(god, type)
        if type == 'github':
            github.sync(god, False)
            data = getattr(god, type)
        if type == 'instagram':
            instagram.sync(god, False)
            data = getattr(god, type)
        if type == 'tumblr':
            tumblr.sync(god, False)
            data = getattr(god, type)
    session.commit()
    return jsonify(data)
    '''

        if god[type].get('count'):
            info = god[type]
        else:
            if type == 'twitter':
                import twitter
                twitter.getTwitterUser(name, name)
            if type == 'github':
                import github
                github.getGithubUser(name, name)
            if type == 'instagram':
                import instagram
                instagram.loop(name)  # 用的是爬虫, 单取 user 意义不大
            if type == 'tumblr':
                import tumblr
                tumblr.getTumblrUserNotSaveKey(name, name)
            if type == 'facebook':
                import facebook
                facebook.getFacebookUser(name, name)
            info = god_oper.getTheGodInfoByName(name, self.current_user)[type]
        self.data.info = info
        self.write(json.dumps(self.data, cls=json_bz.ExtEncoder))
        '''


@app.route('/api_god', methods=['GET', 'PUT', 'POST'])
def api_god():
    user_id = cookie['user_id']
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        cat = data.get('cat', '大杂烩')
        god = session.query(model.God).filter(
            model.God.name.ilike(name)).one_or_none()
        if god:
            if cat != '大杂烩':
                god.cat = cat
        else:
            god_oper.makeSureSocialUnique('twitter', name),
            god_oper.makeSureSocialUnique('github', name),
            god_oper.makeSureSocialUnique('instagram', name),
            god_oper.makeSureSocialUnique('tumblr', name),
            god = model.God(
                name=name,
                cat=cat,
                twitter={'name': name},
                github={'name': name},
                instagram={'name': name},
                tumblr={'name': name},
                facebook={'name': name},
                who_add=user_id
            )
            session.add(god)
            session.flush()
            session.refresh(god)  # 为了取到 id, 要执行这个
        follow_who_oper.follow(user_id, god.id, make_sure=False)
        data = god_oper.getGod(name, user_id)
        if data:
            data = data._asdict()
        session.commit()
        return jsonify(data)
    if request.method == 'POST':
        god_name = request.args.get('god_name', None)
        data = god_oper.getGod(god_name, user_id)
        if data is None:
            raise Exception('不存在 %s' % god_name)
        return jsonify(data)


@app.route('/api_sp/<burl>')
def api_sp(burl):
    '''
    以前的proxy, 为了 anki 已加入的card 能显示出来, 还是要实现
    '''
    url = url_bz.decodeUrl(burl)
    return redirect('/p/%s' % url, code=303)
    return '0'


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


# @app.errorhandler(Exception)
# def all_exception_handler(error):
#     return exception_bz.getExpInfoAll(True)


if __name__ == '__main__':
    app.debug = True
    app.run()
