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
# from webpy_db import SQLLiteral

import proxy
import anki


class api_sp(proxy.ProxyHandler):

    '''
    create by bigzhu at 15/08/05 22:52:44 加密方式传递url
    '''

    def get(self, secret):
        url = proxy.decodeUrl(secret)
        print ('proxy ', url)
        return super(api_sp, self).get(url)


class api_login_anki(BaseHandler):

    '''
    '''
    @tornado_bz.handleError
    @tornado_bz.mustLoginApi
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
    @tornado_bz.handleError
    @tornado_bz.mustLoginApi
    def post(self):
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)
        front = data['front']
        message_id = data['message_id']
        anki.addCard(front, self.current_user)
        oper.anki_save(message_id, self.current_user)
        self.write(json.dumps(self.data))

    @tornado_bz.handleError
    @tornado_bz.mustLoginApi
    def get(self):
        self.set_header("Content-Type", "application/json")
        sql = 'select user_name, password from anki where user_id=$user_id'
        datas = pg.query(sql, vars={'user_id': self.current_user})
        if datas:
            data = datas[0]
        else:
            data = None
        self.write(json.dumps({'error': '0', 'anki': data}, cls=json_bz.ExtEncoder))


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
    print (port)

    web_class = tornado_bz.getAllWebBzRequestHandlers()
    web_class.update(globals().copy())

    url_map = tornado_bz.getURLMap(web_class)
    # 机器人
    # url_map.append((r'/robots.txt()', tornado.web.StaticFileHandler, {'path': "./static/robots.txt"}))
    # sitemap
    # url_map.append((r'/sitemap.xml()', tornado.web.StaticFileHandler, {'path': "./static/sitemap.xml"}))

    url_map.append((r"/app/(.*)", NoCacheHtmlStaticFileHandler, {"path": "../", "default_filename": "index.html"}))
    url_map.append((r'/web_socket', web_socket))
    url_map.append((r'/biography.html', biography))
    url_map.append((r'/', main))
    # url_map.append((r'/static/(.*)', tornado.web.StaticFileHandler, {'path': "./static"}))

    settings = tornado_bz.getSettings()
    settings["pg"] = pg
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
