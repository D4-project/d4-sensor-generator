#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import json
import redis
import flask
import datetime
import configparser

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, send_file, escape

# Import Blueprint
from blueprints.root import root

json_type_description_path = os.path.join(os.environ['D4G_HOME'], 'static/json/type.json')

# get file config
config_file_server = os.path.join(os.environ['D4G_HOME'], 'configs/server.conf')
config_server = configparser.ConfigParser()
config_server.read(config_file_server)

baseUrl = config_server['Server'].get('baseUrl')
if baseUrl == '/':
    baseUrl = ''


app = Flask(__name__, static_url_path=baseUrl+'/static/')
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024

# =========  BLUEPRINT  =========#
app.register_blueprint(root, url_prefix=baseUrl)
# =========       =========#


# ========== ERRORS ============

# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=7200, threaded=True)
