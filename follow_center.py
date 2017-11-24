#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")
import json
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
from model import God, FollowWho, Anki
from model_bz import OauthInfo
from sqlalchemy import and_, func, desc
import datetime
import message
import god
all_message = db_bz.getReflect('all_message')
from db_bz import session


class api_last(tornado_bz.BaseHandler):

    @tornado_bz.handleErrorJson
    def put(self):
        '''
        记录看到这一条的时间, 并返回未读数
        '''
        self.set_header("Content-Type", "application/json")
        data = json.loads(self.request.body)
        last = data.get('last')
        last = time_bz.unicodeToDateTIme(last)

        user_id = self.current_user
        if user_id is None:
            self.finish()
            return
        last_info = dict(updated_at=last)
        session = db_bz.getSession()
        db_bz.updateOrInsert(session, model.Last, last_info, user_id=user_id)

        unread_message_count = message.getUnreadCount(user_id, last)

        session.commit()
        session.close()
        self.write(str(unread_message_count))


class api_collect(BaseHandler):
    '''
    create by bigzhu at 16/05/20 14:17:20 收藏
    '''

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def post(self):
        self.set_header("Content-Type", "application/json")
        parm = json.loads(self.request.body)
        message_id = parm['message_id']
        collect_oper.collect(message_id, self.current_user)
        self.write(json.dumps({'error': '0'}))

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def delete(self, id):
        self.set_header("Content-Type", "application/json")
        count = pg.delete(
            'collect',
            where="user_id='%s' and message_id=%s" % (self.current_user, id))
        if count != 1:
            raise Exception('没有正确的uncollect, uncollect %s 条' % count)
        self.write(json.dumps({'error': '0'}))

    @tornado_bz.handleErrorJson
    @tornado_bz.mustLoginJson
    def get(self):
        self.set_header("Content-Type", "application/json")
        user_id = self.current_user

        sql = session.query(all_message).subquery()
        sql = message.addCollectInfo(sql, user_id)
        sql = message.addAnkiInfo(sql, user_id)
        data = session.query(sql).filter(sql.c.collect.isnot(None)).order_by(
            sql.c.collect_at).all()
        data = [r._asdict() for r in data]

        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class api_gods(BaseHandler):
    '''
    create by bigzhu at 16/12/11 22:32:39 公开推荐的god
    '''

    @tornado_bz.handleErrorJson
    def get(self):
        """
        @apiGroup god
        @api {get} /api_gods 推荐关注的人
        @apiParam {String} cat 分类
        @apiParam {String} before 早于这个时间的(取更多)
        @apiParam {Number} limit 一次取几个
        @apiParam {Boolean} followed 已关注, 否则为推荐
        """

        self.set_header("Content-Type", "application/json")
        cat = self.get_argument('cat', None)
        before = self.get_argument('before', None)
        limit = self.get_argument('limit', 6)
        followed = self.get_argument('followed', False)
        user_id = self.current_user

        q = session.query(God)
        if cat:
            q = q.filter(God.cat == cat)
        if before:
            q = q.filter(God.created_at < before)
        if not followed:
            q = q.filter(God.is_public == 1)
        # 只看本人关注的
        elif user_id:
            my_god = session.query(
                FollowWho.god_id).filter(FollowWho.user_id == user_id)
            q = q.filter(God.id.in_(my_god))
        else:
            raise Exception('未登录, 无法看私人关注!')

        # 空god过滤
        sub_sql = god.filterAllNullGod(q.subquery())
        # 关注数
        sub_sql = god.addGodFollowedCount(sub_sql)
        # 取 admin remark
        sub_sql = god.addAdminRemark(sub_sql)
        if user_id:
            sub_sql = god.addUserFollowedInfo(sub_sql, user_id)

        data = session.query(sub_sql).order_by(
            desc(sub_sql.c.created_at)).limit(limit).all()

        data = [r._asdict() for r in data]
        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class api_cat(BaseHandler):
    @tornado_bz.handleErrorJson
    def get(self):
        """
        查出 god 分类
        """
        self.set_header("Content-Type", "application/json")
        is_my = self.get_argument('is_my', 0)
        user_id = self.current_user

        q = session.query(God)
        if is_my:
            my_god = session.query(
                FollowWho.god_id).filter(FollowWho.user_id == user_id)
            q = q.filter(God.id.in_(my_god))
        else:
            q = q.filter(God.is_public == 1)
            if user_id is None:
                q = q.filter(God.cat != '18+')

        sub_sql = god.filterAllNullGod(q.subquery())
        sub_sql = god.addGodFollowedCount(sub_sql)

        data = session.query(
            func.count(sub_sql.c.cat).label('count'), sub_sql.c.cat).group_by(
                sub_sql.c.cat).all()

        data = [r._asdict() for r in data]

        self.write(json.dumps(data, cls=json_bz.ExtEncoder))


class api_login(BaseHandler):
    @tornado_bz.handleErrorJson
    def post(self):
        self.set_header("Content-Type", "application/json")
        login_info = json.loads(self.request.body)
        user_name = login_info.get("user_name")
        # password = login_info.get("password")
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
        self.set_header("Content-Type", "application/json")

        after = self.get_argument('after', None)  # 晚于这个时间的
        limit = self.get_argument('limit', 10)
        search_key = self.get_argument('search_key', None)
        god_name = self.get_argument('god_name', None)

        user_id = self.current_user
        unread_message_count = 0

        if after:
            after = time_bz.unicodeToDateTIme(after)
        elif search_key is None and god_name is None:  # 不按 search 和 god 查时, 登录了取 last
            after = session.query(model.Last.updated_at).filter(
                model.Last.user_id == user_id).one_or_none()
            if after is None:  # 未登录或者没有last, 取最近两天
                after = datetime.date.today() - datetime.timedelta(days=6)

        sub_sql = session.query(all_message).subquery()

        if user_id:
            sub_sql = message.addCollectInfo(sub_sql, user_id)
            sub_sql = message.addAnkiInfo(sub_sql, user_id)
        else:
            # 不要 18+ 的
            sub_sql = session.query(all_message).filter(
                all_message.c.cat != '18+').subquery()
            # 只要 public 的
            sub_sql = session.query(sub_sql).filter(
                sub_sql.c.god_name.in_(
                    session.query(God.name).filter(God.is_public.in_(
                        [1, 2])))).subquery()

        # after = None
        # 查比这个时间新的
        if after:
            sub_sql = session.query(sub_sql).filter(
                sub_sql.c.out_created_at > after).subquery()

        # 互斥的filter_bz.filter
        if god_name:
            sub_sql = session.query(sub_sql).filter(
                sub_sql.c.god_name == god_name)
        elif search_key:
            # jsonb 没找到办法做like
            #query = session.query(query).filter(or_(query.c.text.ilike('%%%s%%' % search_key), query.c.content.astext.like('%%%s%%' % search_key))).subquery()
            sub_sql = session.query(sub_sql).filter(
                or_(sub_sql.c.text.ilike('%%%s%%' % search_key))).subquery()
        elif user_id:  # 没那几个, 又有 user_id, 只查关注了的
            # 查出还有多少未读
            if after:
                unread_message_count = message.getUnreadCount(user_id, after)

            sub_sql = message.filterFollowed(sub_sql, user_id)

        sub_sql = session.query(sub_sql).order_by(
            sub_sql.c.out_created_at).limit(limit)
        messages = sub_sql.all()
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
        '''
        设置 anki 用户及密码
        '''
        self.set_header("Content-Type", "application/json")
        user_id = self.current_user
        session = db_bz.getSession()
        data = json.loads(self.request.body)
        anki_info = dict(
            user_id=user_id,
            user_name=data['user_name'],
            password=data['password'],
            csrf_token=None,
            mid=None,
            cookie=None)
        db_bz.updateOrInsert(session, Anki, anki_info, user_id=user_id)
        session.commit()
        session.colse()


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
        #oper.anki_save(message_id, self.current_user)
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
        port = 9445
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
