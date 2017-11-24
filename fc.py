#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append("../lib_py")

from flask import Flask
from flask import make_response
from flask import jsonify
from db_bz import session
import db_bz
import model
import json
import json_bz
from flask_bz import ExtEncoder

all_message = db_bz.getReflect('all_message')


app = Flask(__name__)
app.json_encoder = ExtEncoder


@app.route('/')
def api_new():
    data = session.query(model.Message).limit(20).all()
    # data = [r._asdict() for r in data]
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
