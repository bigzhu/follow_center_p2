#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
sys.path.append("../lib_py")
import json_bz
from sqlalchemy import or_

import db_bz
import tornado.ioloop
import tornado.web
import tornado_bz
from tornado_bz import BaseHandler

import tornado_web_bz
import time_bz

import model
import anki
import proxy
import filter
from model import Collect, AnkiSave, God, FollowWho
from model_bz import OauthInfo
from sqlalchemy import and_, func
all_message = db_bz.getReflect('all_message')


class api_cat(BaseHandler):
    @tornado_bz.handleErrorJson
    def get(self):
        """
        查出 god 分类
        """
        self.set_header("Content-Type", "application/json")
        is_my = self.get_argument('is_my', 0)
        user_id = self.current_user
        session = db_bz.getSession()
        ## 所有 social 都是空的废 god
        null_god = session.query(God.id).filter(
            and_(
                God.tumblr.is_(None), God.twitter.is_(None),
                God.github.is_(None), God.instagram.is_(None)))
        ## 空的不查
        sql = session.query(God).filter(~God.id.in_(null_god))
        if is_my:
            my_god = session.query(
                FollowWho.god_id).filter(FollowWho.user_id == user_id)
            sql = sql.filter(God.id.in_(my_god))
        else:
            sql = sql.filter(God.is_public == 1)
            if user_id is None:
                sql = sql.filter(God.cat != '18+')
        sub_sql = sql.subquery()

        data = session.query(func.count(sub_sql.c.cat).label('count'),
                             sub_sql.c.cat).group_by(sub_sql.c.cat).all()

        data = [r._asdict() for r in data]

        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class api_login(BaseHandler):
    @tornado_bz.handleErrorJson
    def post(self):
        self.set_header("Content-Type", "application/json")
        login_info = json.loads(self.request.body)
        user_name = login_info.get("user_name")
        # password = login_info.get("password")
        session = db_bz.getSession()
        user_info = session.query(OauthInfo).filter(
            OauthInfo.name == user_name,
            OauthInfo.type == 'github').one_or_none()
        if user_info is None:
            raise Exception('没有用户 %s' % user_name)
        self.set_secure_cookie("user_id", str(user_info.id))
        self.write(json.dumps({'error': '0'}))


class api_registered(BaseHandler):
    '''
    注册的用户数
    '''

    @tornado_bz.handleErrorJson
    def get(self):
        self.set_header("Content-Type", "application/json")
        session = db_bz.getSession()
        registered_count = session.query(OauthInfo).count()
        self.write(
            json.dumps(
                {
                    'registered_count': registered_count
                }, cls=json_bz.ExtEncoder))


class api_new(BaseHandler):
    """
        create by bigzhu at 15/08/17 11:12:24 查看我订阅了的message，要定位到上一次看的那条
        modify by bigzhu at 15/11/17 16:22:05 最多查1000出来
        modify by bigzhu at 15/11/17 19:18:25 不要在这里限制条目数
        modify by bigzhu at 16/02/21 10:02:25 改为get
        modify by bigzhu at 16/04/29 14:54:37 支持关键字查找
        modify by bigzhu at 16/05/28 23:10:05 重构

        @apiGroup message
        @api {get} /api_new 取新的社交信息
        @apiParam {String} after 只查在这个时间以后的
        @apiParam {Number} limit 数量限制
        @apiParam {String} search_key 搜索关键字
        @apiParam {String} god_name 只看这个人的
    """

    def get(self, parm=None):
        session = db_bz.getSession()

        self.set_header("Content-Type", "application/json")

        after = self.get_argument('after', None)  # 晚于这个时间的
        limit = self.get_argument('limit', 10)
        search_key = self.get_argument('search_key', None)
        god_name = self.get_argument('god_name', None)

        user_id = self.current_user

        unread_message_count = 0
        if after:
            after = time_bz.timestampToDateTime(after, True)
        elif search_key is None and god_name is None:  # 按 search 和 god 查时, 不必取 last
            after = session.query(model.Last.updated_at).filter(
                model.Last.user_id == user_id).all()
            if after:
                after = after[0]
            else:
                after = None

        if user_id:
            # 取出未读的数量
            # 取出这个用户的收藏
            collect_sq = session.query(Collect).filter(
                Collect.user_id == user_id).subquery()
            # 附加收藏到 message 里
            query = session.query(
                all_message, collect_sq.c.message_id.label('collect'),
                collect_sq.c.created_at.label('collect_at')).outerjoin(
                    collect_sq,
                    all_message.c.id == collect_sq.c.message_id).subquery()
            # 取出这个用户的anki
            anki_sq = session.query(AnkiSave).filter(
                AnkiSave.user_id == user_id).subquery()
            # 附加 anki 到 message
            query = session.query(
                query, anki_sq.c.message_id.label('anki'),
                anki_sq.c.created_at.label('anki_at')).outerjoin(
                    anki_sq, query.c.id == anki_sq.c.message_id).subquery()
        else:
            # 不要 18+ 的
            query = session.query(all_message).filter(
                all_message.c.cat != '18+').subquery()
            # 只要 public 的
            query = session.query(query).filter(
                query.c.god_name.in_(
                    session.query(God.name).filter(God.is_public.in_(
                        [1, 2])))).subquery()

        # after = None
        # 查比这个时间新的
        if after:
            query = session.query(query).filter(
                query.c.out_created_at > after).subquery()

        # 互斥的filter_bz.filter
        if god_name:
            query = session.query(query).filter(query.c.god_name == god_name)
        elif search_key:
            # jsonb 没找到办法做like
            #query = session.query(query).filter(or_(query.c.text.ilike('%%%s%%' % search_key), query.c.content.astext.like('%%%s%%' % search_key))).subquery()
            query = session.query(query).filter(
                or_(query.c.text.ilike('%%%s%%' % search_key))).subquery()
        elif user_id:  # 没那几个, 又有 user_id, 只查关注了的
            ## 查出还有多少未读
            if after:
                unread_query = filter.filterFollowedMessage(
                    all_message, session, user_id)
                unread_query = session.query(unread_query).filter(
                    unread_query.c.out_created_at > after).subquery()
                unread_message_count = session.query(unread_query).count()

            query = filter.filterFollowedMessage(query, session, user_id)

        # query = session.query(query).order_by(query.c.out_created_at).limit(limit)
        query = session.query(query).order_by(
            query.c.out_created_at).limit(limit)
        #print(query.statement.compile(compile_kwargs={"literal_binds": True}))
        messages = query.all()
        messages = [r._asdict() for r in messages]
        data = dict(
            messages=messages, unread_message_count=unread_message_count)

        if (len(messages) == 0):
            if (user_id):
                data['followed_god_count'] = session.query(FollowWho).filter(
                    FollowWho.user_id == user_id).count()
            else:
                data['followed_god_count'] = 0

        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class web_socket(tornado_web_bz.web_socket):
    pass


class api_sp(proxy.ProxyHandler):
    '''
    create by bigzhu at 15/08/05 22:52:44 加密方式传递url
    '''

    def get(self, secret):
        url = proxy.decodeUrl(secret)
        print('proxy ', url)
        return super(api_sp, self).get(url)


class api_login_anki(BaseHandler):
    '''
    '''

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def post(self):
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)
        anki_info = storage()
        anki_info.user_name = data['user_name']
        anki_info.password = data['password']
        anki_info.user_id = self.current_user
        db_bz.insertOrUpdate(pg, 'anki', anki_info,
                             "user_id='%s'" % anki_info.user_id)
        anki.getMidAndCsrfTokenHolder(anki_info.user_id, reset_cookie=True)
        self.write(json.dumps(self.data))


class api_anki(BaseHandler):
    '''
    '''

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def post(self):
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)
        front = data['front']
        message_id = data['message_id']
        anki.addCard(front, self.current_user)
        oper.anki_save(message_id, self.current_user)
        self.write(json.dumps(self.data))

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def get(self):
        """
        @api {get} /api_anki 取anki用户信息
        @apiGroup anki
        @apiSuccess {Number} id id
        @apiSuccess {String} name anki 用户名
        """
        self.set_header("Content-Type", "application/json")
        # sql = 'select user_name, password from anki where user_id=$user_id'
        print(self.current_user)
        data = anki.getAnkiConfig(self.current_user)
        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class NoCacheHtmlStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        if path == '':
            # self.set_header("Cache-control", "no-cache")
            self.set_header("Cache-control",
                            "no-store, no-cache, must-revalidate, max-age=0")


if __name__ == "__main__":

    debug = None
    if len(sys.argv) == 3:
        port = int(sys.argv[1])
        debug = sys.argv[2]
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 9444
    print(port)

    web_class = tornado_bz.getAllWebBzRequestHandlers()
    web_class.update(globals().copy())

    url_map = tornado_bz.getURLMap(web_class)
    # 机器人
    # url_map.append((r'/robots.txt()', tornado.web.StaticFileHandler, {'path': "./static/robots.txt"}))
    # sitemap
    # url_map.append((r'/sitemap.xml()', tornado.web.StaticFileHandler, {'path': "./static/sitemap.xml"}))

    url_map.append((r"/app/(.*)", NoCacheHtmlStaticFileHandler, {
        "path": "../",
        "default_filename": "index.html"
    }))
    url_map.append((r'/web_socket', web_socket))
    # url_map.append((r'/static/(.*)', tornado.web.StaticFileHandler, {'path': "./static"}))

    settings = tornado_bz.getSettings()
    # settings["pg"] = pg
    if debug:
        settings["disable_sp"] = True
    else:
        settings["disable_sp"] = None
    settings["login_url"] = "/app/login.html"
    # settings, wechat = wechat_oper.initSetting(settings)
    application = tornado.web.Application(url_map, **settings)

    application.listen(port)
    ioloop = tornado.ioloop.IOLoop().instance()

    tornado.autoreload.start(ioloop)
    ioloop.start()
