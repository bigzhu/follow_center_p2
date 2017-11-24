#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

from flask import Flask
from flask import request
# from flask import make_response
from flask import jsonify
from flask_bz import ExtEncoder
import message


app = Flask(__name__)
app.json_encoder = ExtEncoder


@app.route('/api_new')
def api_new():

    after = request.args.get('after', None)  # 晚于这个时间的
    limit = request.args.get('limit', 10)
    search_key = request.args.get('search_key', None)
    god_name = request.args.get('god_name', None)
    data = message.getNew(None, after, limit, search_key, god_name)
    return jsonify(data)


@app.route('/projects/')
def projects():
    return 'The project page'


@app.route('/about')
def about():
    return 'The about page'


if __name__ == '__main__':
    app.debug = True
    app.run()
