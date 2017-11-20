#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
sys.path.append("../lib_py")
import json_bz

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


class api_new(BaseHandler):
    '''
    create by bigzhu at 15/08/17 11:12:24 查看我订阅了的message，要定位到上一次看的那条
    modify by bigzhu at 15/11/17 16:22:05 最多查1000出来
    modify by bigzhu at 15/11/17 19:18:25 不要在这里限制条目数
    modify by bigzhu at 16/02/21 10:02:25 改为get
    modify by bigzhu at 16/04/29 14:54:37 支持关键字查找
    modify by bigzhu at 16/05/28 23:10:05 重构
    '''

    def get(self, parm=None):
        session = db_bz.getSession()

        self.set_header("Content-Type", "application/json")
        after = None
        limit = None
        search_key = None
        god_name = None
        if parm:
            parm = json.loads(parm)
            after = parm.get('after')  # 晚于这个时间的
            limit = parm.get('limit')
            search_key = parm.get('search_key')
            god_name = parm.get('god_name')  # 只查这个god

        user_id = self.current_user
        if after:
            after = time_bz.timestampToDateTime(after, True)
        elif search_key is None and god_name is None:  # 按 search 和 god 查时, 不必取 last
            after = session.query(model.Last.updated_at).filter(model.Last.user_id == user_id).all()
            if after:
                after = after[0]
            else:
                after = None

        messages = public_db.getNewMessages(user_id=user_id, after=after, limit=limit, god_name=god_name, search_key=search_key)
        data = dict(messages=messages, unread_message_count=oper.getUnreadCount(user_id))
        if (len(messages) == 0):
            if (user_id):
                data['followed_god_count'] = god_oper.getFollowedGodCount(user_id)
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
        db_bz.insertOrUpdate(pg, 'anki', anki_info, "user_id='%s'" % anki_info.user_id)
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
            self.set_header("Cache-control", "no-store, no-cache, must-revalidate, max-age=0")


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

    url_map.append((r"/app/(.*)", NoCacheHtmlStaticFileHandler, {"path": "../", "default_filename": "index.html"}))
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
