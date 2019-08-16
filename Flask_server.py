#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import uuid
import time
import json
import redis
import flask
import secrets
import datetime
import requests
import ipaddress
import configparser

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging
import logging.handlers

root = logging.getLogger()

log_filename = 'logs/sensor-generator.log'
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler_log = logging.handlers.TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
handler_log.suffix = '%Y-%m-%d.log'
handler_log.setFormatter(formatter)
handler_log.setLevel(logging.DEBUG)
root.addHandler(handler_log)

from io import BytesIO
import zipfile

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, send_file

baseUrl = ''
if baseUrl != '':
    baseUrl = '/'+baseUrl

json_type_description_path = os.path.join(os.environ['D4G_HOME'], 'static/json/type.json')

# get file config
config_file_server = os.path.join(os.environ['D4G_HOME'], 'configs/server.conf')
config_server = configparser.ConfigParser()
config_server.read(config_file_server)

D4_API_KEY = config_server['D4_API'].get('D4_API_KEY')
D4_Server = config_server['D4_API'].get('D4_Server')

with open(json_type_description_path, 'r') as f:
    json_type = json.loads(f.read())
json_type_description = {}
for type_info in json_type:
    json_type_description[type_info['type']] = type_info

app = Flask(__name__, static_url_path=baseUrl+'/static/')
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024


email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
email_regex = re.compile(email_regex)

# ========== FUNCTIONS ============
def generate_uuid():
    return str(uuid.uuid4())

def generate_secret_key():
    return secrets.token_urlsafe(256)

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def check_email(email):
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

def get_json_type_description():
    return json_type_description.copy()

def register_sensor_via_api(sensor_uuid, hmac_key, mail=None):
    res = requests.post("{}/api/v1/add/sensor/register".format(D4_Server), json={"uuid": sensor_uuid, "hmac_key": hmac_key}, headers={'Authorization': D4_API_KEY}, verify=False)
    print(res.status_code)

    if res.status_code == 200:
        root.info('Sensor registred, uuid: {}'.format(sensor_uuid))
    else:
        root.error(res.json())

def create_go_client_zip():

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "a") as zf:
        for dirpath, dirnames, filenames in os.walk('d4-goclient'):
            for client_file in filenames:
                with open(os.path.join( dirpath, client_file), 'br') as fg:
                    file_content = fg.read()
                    zf.writestr( os.path.join(dirpath, client_file), BytesIO(file_content).getvalue())

    zip_buffer.seek(0)
    return zip_buffer

def create_c_client_zip():

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "a") as zf:
        for dirpath, dirnames, filenames in os.walk('d4-core/client'):
            for client_file in filenames:
                with open(os.path.join( dirpath, client_file), 'br') as fg:
                    file_content = fg.read()
                    zf.writestr( os.path.join(dirpath.replace('d4-core', '', 1), client_file), BytesIO(file_content).getvalue())

    zip_buffer.seek(0)
    return zip_buffer

# destination
# key
# snaplen
# source
# type
# uuid
# version
def create_config_file(UUID, d4_type, destination, key, d4_client='go', os_client=None, arch=None):

    snaplen = b'4096'
    version = b'1'
    source = b'stdin'

    ## TODO: add 254 type
    try:
        d4_type = int(d4_type)
        if d4_type < MIN_D4_TYPE or d4_type > MAX_D4_TYPE:
            d4_type = 8
    except:
        d4_type = 8

    if d4_client=='c':
        dirname = 'client'
        destination = 'stdout'
        compiled_file = None
    else:
        dirname = 'd4-goclient'
        compiled_file = None
        if destination=='default':
            destination = 'crq.circl.lu:4443'
        else:
            if is_valid_ip(destination):
                destination = '{}:4443'.format(destination)
            else:
                destination = 'crq.circl.lu:4443'
        if os_client and arch:
            if os_client in dict_go_exe:
                if arch in dict_go_exe[os_client]:
                    compiled_file = dict_go_exe[os_client][arch]

    zip_buffer = BytesIO()


    with zipfile.ZipFile(zip_buffer, "a") as zf:

        zf.writestr( '{}/configs/destination'.format(dirname), BytesIO(destination.encode()).getvalue())
        zf.writestr( '{}/configs/key'.format(dirname), BytesIO(key.encode()).getvalue())
        zf.writestr( '{}/configs/snaplen'.format(dirname), BytesIO(snaplen).getvalue())
        zf.writestr( '{}/configs/source'.format(dirname), BytesIO(source).getvalue())
        zf.writestr( '{}/configs/type'.format(dirname), BytesIO(str(d4_type).encode()).getvalue())
        zf.writestr( '{}/configs/uuid'.format(dirname), BytesIO(UUID.encode()).getvalue())
        zf.writestr( '{}/configs/version'.format(dirname), BytesIO(version).getvalue())

        if compiled_file:
            with open(compiled_file, 'rb') as fcomp:
                content = fcomp.read()
                zf.writestr( '{}/{}'.format(dirname, os.path.basename(compiled_file)), BytesIO(content).getvalue())
            with open(os.path.join(os.environ['D4G_HOME'], 'sha256sum.txt'), 'rb') as fsha:
                content = fsha.read()
                zf.writestr( '{}/sha256sum.txt'.format(dirname), BytesIO(content).getvalue())

    zip_buffer.seek(0)
    return zip_buffer

def load_go_ex():
    dict_go_exe = {}
    for dirpath, dirnames, filenames in os.walk('exe_goclient'):
        for go_client in filenames:
            client = go_client.split('_')
            if not client[1] in dict_go_exe:
                dict_go_exe[client[1]] = {}
            dict_go_exe[client[1]][client[2]] = os.path.join(os.environ['D4G_HOME'], dirpath, go_client)
    return dict_go_exe

# ========== ERRORS ============

# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404

# ========== ROUTES ============

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template("index.html")

@app.route('/client', methods=['POST', 'GET'])
def client():
    return render_template("d4-client.html")

@app.route('/go-client', methods=['GET'])
def go_client():
    return render_template("d4-go.html", dict_go_exe=dict_go_exe)

@app.route('/type', methods=['POST', 'GET'])
def type():
    d4_client = request.args.get('d4_client')
    os_client = request.args.get('os')
    arch = request.args.get('arch')

    #d4_client = 'c'

    json_type_description = get_json_type_description()
    json_type_description.pop(0)

    # # TODO: add extended types
    # remove unsupported types
    if d4_client == 'c':
        json_type_description.pop(2)
        json_type_description.pop(254)

    return render_template("d4-type.html", json_type_description=json_type_description, d4_client=d4_client, os_client=os_client, arch=arch)

@app.route('/destination', methods=['GET', 'POST'])
def destination():
    destination = request.form.get('destination')
    if destination:
        d4_client = request.form.get('d4_client')
        destination = request.form.get('destination')
        os_client = request.form.get('os')
        arch = request.form.get('arch')
        d4_type = request.form.get('type')

        if not is_valid_ip(destination):
            return render_template("d4-destination.html", d4_client=d4_client, d4_type=d4_type, os_client=os_client, arch=arch, error='Invalid IP Address')
        else:
            return redirect(url_for('download_page', d4_client=d4_client, type=d4_type, destination=destination, os_client=os_client, arch=arch))

    d4_client = request.args.get('d4_client')
    d4_type = request.args.get('type')
    os_client = request.args.get('os')
    arch = request.args.get('arch')

    return render_template("d4-destination.html", d4_client=d4_client, d4_type=d4_type, os_client=os_client, arch=arch)

@app.route('/download_page', methods=['GET'])
def download_page():
    d4_client = request.args.get('d4_client')
    d4_type = request.args.get('type')
    os_client = request.args.get('os')
    arch = request.args.get('arch')
    destination = request.args.get('destination')
    return render_template("download.html", d4_client=d4_client, d4_type=d4_type, os_client=os_client, arch=arch, destination=destination)

@app.route('/download', methods=['GET'])
def download():

    ip_address = request.remote_addr

    d4_client = request.args.get('d4_client')
    d4_type = request.args.get('type')
    destination = request.args.get('destination')
    mail = request.args.get('mail')

    os_client = request.args.get('os')
    arch = request.args.get('arch')

    if not d4_client or not d4_type or not destination:
        return redirect(url_for('client'))

    # verify type
    ## TODO: add 254 type
    try:
        d4_type = int(d4_type)
        if d4_type < MIN_D4_TYPE or d4_type > MAX_D4_TYPE:
            return redirect(url_for('client'))
    except:
        return redirect(url_for('client'))



    UUID = generate_uuid()
    key = generate_secret_key()

    filename = 'd4-sensor-client.zip'

    message = 'New Sensor created, uuid:{}, ip:{}, type:{}, destination:{}, client:{}'.format(UUID, ip_address, d4_type, destination, d4_client)
    if mail:
        message = message + ', mail:{}'.format(mail)
    if os_client:
        message = message + ', os:{}, arch:{}'.format(os_client, arch)

    root.warning(message)

    if d4_client=='c':
        zip_file0= create_c_client_zip()
    else:
        zip_file0= create_go_client_zip()
    zip_file= create_config_file(UUID, d4_type, destination, key, d4_client=d4_client, os_client=os_client, arch=arch)

    with zipfile.ZipFile(zip_file0, "a") as zf:
        with zipfile.ZipFile(zip_file, "a") as zfc:
            [zfc.writestr(t[0], t[1].read()) for t in ((n, zf.open(n)) for n in zf.namelist())]

    zip_file.seek(0)

    # register sensor
    if destination == 'default':
        register_sensor_via_api(UUID, key)

    return send_file(zip_file, attachment_filename=filename, as_attachment=True)

if __name__ == "__main__":
    g_json_type_description = get_json_type_description()
    g_json_type_description.pop(0)
    g_json_type_description.pop(254)

    MIN_D4_TYPE = min(json_type_description, key=int)
    MAX_D4_TYPE = max(json_type_description, key=int)

    dict_go_exe = load_go_ex()

    app.run(host='0.0.0.0', port=7200, threaded=True)
