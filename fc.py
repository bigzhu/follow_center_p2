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
import time_bz
import follow_who_oper
from sync import twitter as twitter_sync
from sync import instagram as instagram_sync
from sync import tumblr as tumblr_sync
from sync import github as github_sync
import exception_bz
import collect_oper
import oauth_conf
from flask_oauthlib.client import OAuth, OAuthException
import datetime

# from flask.json import JSONEncoder


class CustomJSONEncoder(ExtEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return time_bz.datetimeTOJson(obj)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return ExtEncoder.default(self, obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.secret_key = conf.cookie_secret
# js 需要访问 cookies
app.config['SESSION_COOKIE_HTTPONLY'] = False
oauth = OAuth(app)

twitter = oauth_conf.getTwitter(app)
github = oauth_conf.getGithub(app)
qq = oauth_conf.getQQ(app)
facebook = oauth_conf.getFacebook(app)

from gold import trade


#@api.errorhandler
# def default_error_handler(error):
#    '''Default error handler'''
#    return {'error_info': str(error)}, getattr(error, 'code', 500)


@app.route('/api_message', methods=['GET'])
def api_message():
    user_id = cookie['user_id']
    if request.method == 'GET':
        id = request.args.get('id', None)
        data = message_oper.getByID(user_id, id)
        return jsonify(data)


@app.route('/api_test', methods=['POST'])
def api_test():
    '''
    the gold
    '''
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        return jsonify({"result": "Success"})


@app.route('/api_trade')
def api_trade():
    type = request.args.get('type', None)
    gold_conf = session.query(model.Gold).filter(
        model.Gold.type == type).one_or_none()
    print(gold_conf)
    result = trade(gold_conf.oper, gold_conf.max,
                   gold_conf.atr, gold_conf.last_reverse_max, gold_conf.week_atr)
    return jsonify(result)


@app.route('/api_trade_conf', methods=['GET', 'POST'])
def api_trade_conf():
    '''
    期货跟踪
    '''
    user_id = cookie['user_id']
    if request.method == 'POST':
        data = request.get_json()
        data['user_id'] = user_id
        data['updated_at'] = datetime.datetime.utcnow()
        data['max'] = data['max'] * 1000
        data['atr'] = data['atr'] * 1000
        data['week_atr'] = data['week_atr'] * 1000
        data['last_reverse_max'] = data['last_reverse_max'] * 1000
        db_bz.updateOrInsert(model.Gold, data, type=data['type'])
        session.commit()
        return jsonify("0")
    if request.method == 'GET':
        type = request.args.get('type', None)
        gold_conf = session.query(model.Gold).filter(
            model.Gold.type == type).one_or_none()
        print(session.query(model.Gold).filter(model.Gold.type == type))
        if gold_conf is not None:
            gold_conf.max = gold_conf.max / 1000
            gold_conf.atr = gold_conf.atr / 1000
            gold_conf.week_atr = gold_conf.week_atr / 1000
            gold_conf.last_reverse_max = gold_conf.last_reverse_max / 1000
        return jsonify(gold_conf)


@facebook.tokengetter
def get_facebook_oauth_token():
    return cookie.get('oauth_token')


@app.route('/api_facebook_oauthorized')
def api_facebook_oauthorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    cookie['oauth_token'] = (resp['access_token'], '')
    user = facebook.get('/me?fields=id,name,locale,email').data
    oauth_info = dict(
        out_id=user['id'],
        type='facebook',
        name=user['name'],
        avatar='https://graph.facebook.com/%s/picture?height=250' % user['id'],
        email=user.get('email'),
        location=user['locale']
    )
    oauth_info, is_insert = oauth_bz.saveAndGetOauth(oauth_info)
    cookie['user_id'] = str(oauth_info.id)
    session.commit()
    return redirect('/')


@app.route('/api_facebook')
def api_facebook():
    callback = url_for(
        'api_facebook_oauthorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


@qq.tokengetter
def get_qq_oauth_token():
    return cookie.get('qq_token')


@app.route('/api_qq_info')
def api_qq_info():
    if 'qq_token' in cookie:
        data = oauth_conf.update_qq_api_request_data()
        resp = qq.get('/user/get_user_info', data=data)
        if resp.status == 200:
            user = oauth_conf.json_to_dict(resp.data)
            oauth_info = dict(
                out_id=0,
                type='qq',
                name=user['nickname'],
                avatar=user['figureurl_qq_2'],
                email=user.get('email'),
                location=user.get('province') + user.get('city')
            )

            oauth_info, is_insert = oauth_bz.saveAndGetOauth(oauth_info)
            cookie['user_id'] = str(oauth_info.id)
            return redirect('/')
        else:
            flash('Unable to load user info from QQ.')


@app.route('/api_qq')  # 回调地址修改要备案
def api_qq_oauthorized():
    resp = qq.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    cookie['qq_token'] = (resp['access_token'], '')

    # Get openid via access_token, openid and access_token are needed for API calls
    resp = qq.get('/oauth2.0/me', {'access_token': cookie['qq_token'][0]})
    resp = oauth_conf.json_to_dict(resp.data)
    if isinstance(resp, dict):
        cookie['qq_openid'] = resp.get('openid')

    return redirect(url_for('api_qq_info'))


@app.route('/api_qq_login')
def api_qq():
    print(url_for('api_qq_oauthorized', _external=True))
    return qq.authorize(callback='https://follow.center/api_qq')


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
            twitter_sync.sync(god, False)
            data = getattr(god, type)
        if type == 'github':
            github_sync.sync(god, False)
            data = getattr(god, type)
        if type == 'instagram':
            instagram_sync.sync(god, False)
            data = getattr(god, type)
        if type == 'tumblr':
            tumblr_sync.sync(god, False)
            data = getattr(god, type)
    session.commit()
    return jsonify(data)


@app.route('/api_god', methods=['GET', 'PUT', 'POST'])
def api_god():
    user_id = cookie.get('user_id')
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
        session.commit()
        return jsonify(data)
    if request.method == 'GET':
        god_name = request.args.get('god_name', None)
        data = god_oper.getGod(god_name, user_id)
        if data is None:
            raise Exception('不存在 %s' % god_name)
        return jsonify(data)
    if request.method == 'PUT':
        data = request.get_json()
        god_oper.updateGod(data)
        session.commit()
        return jsonify("0")


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
    user_id = cookie.get('user_id')
    if user_id is None:
        return jsonify(['github'])
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
    print(data)
    user_name = data['user_name']
    # password = data['password']
    oauth_info = oauth_bz.getOauthInfo(None, user_name, 'github')

    # cookie.permanent = True
    cookie['user_id'] = str(oauth_info.id)

    return jsonify("0")


@app.before_request
def make_session_permanent():
    cookie.permanent = True


@app.route('/api_old')
def api_old():
    before = request.args.get('before')
    not_types = request.args.getlist('not[]')
    god_name = request.args.get('god_name')
    search_key = request.args.get('search_key')
    limit = request.args.get('limit', 10)
    user_id = cookie.get('user_id')
    data = message_oper.getOld(
        user_id, before, limit, search_key, god_name, not_types)
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
    last = time_bz.jsonToDatetime(last)
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
    user_id = cookie.get('user_id')

    if user_id is not None:
        follow_count = follow_who_oper.getFollowCount(user_id)
        if follow_count == 0:
            follow_who_oper.followAll(user_id)
            session.commit()

    data = message_oper.getNew(user_id, after,
                               limit, search_key, god_name, not_types)
    return jsonify(data)


@app.teardown_request
def shutdown_session(exception=None):
    session.remove()


@app.errorhandler(Exception)
def all_exception_handler(error):
    return exception_bz.getExpInfoAll(True), 500


if __name__ == '__main__':
    app.debug = True
    app.run()
