# Copyright (c) 2019 Intel Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Grafana Service
"""

import os
import shutil
import json
import tempfile
import threading
import copy
import math
import queue
import secrets
import ssl
from flask import Flask, render_template, Response, request, session
from jinja2 import Environment, select_autoescape, FileSystemLoader
from distutils.util import strtobool
from distutils.dir_util import copy_tree
import cv2
import numpy as np
import cfgmgr.config_manager as cfg
import eii.msgbus as mb
from util.log import configure_logging
from util.util import Util
from util.common import Visualizer

# Initializing Grafana related variables
TMP_DIR = tempfile.gettempdir()
GRAFANA_DIR = os.path.join(TMP_DIR, "grafana")
CERT_FILE = "{}/server_cert.pem".format(GRAFANA_DIR)
KEY_FILE = "{}/server_key.pem".format(GRAFANA_DIR)
CA_FILE = "{}/ca_cert.pem".format(GRAFANA_DIR)
CONF_FILE = "{}/grafana.ini".format(GRAFANA_DIR)
TEMP_DS = "{}/conf/provisioning/datasources/datasource.yml".format(GRAFANA_DIR)
TEXT = 'Disconnected'
TEXTPOSITION = (10, 110)
TEXTFONT = cv2.FONT_HERSHEY_PLAIN
TEXTCOLOR = (255, 255, 255)

# Config manager initialization
ctx = cfg.ConfigMgr()
app_cfg = ctx.get_app_config()
dev_mode = ctx.is_dev_mode()
topics_list = []
topic_config_list = []
queue_dict = {}

# Initializing logger
log = configure_logging(os.getenv('PY_LOG_LEVEL', 'DEBUG').upper(), __name__,
                        dev_mode)

# Visualization related variables
FRAME_QUEUE_SIZE = 10

# Initializing flask related variables
NONCE = secrets.token_urlsafe(8)
APP = Flask(__name__)
LOADER = FileSystemLoader(searchpath="Grafana/templates/")

# Setting default auto-escape for all templates
ENV = Environment(loader=LOADER, autoescape=select_autoescape(
    enabled_extensions=('html'),
    default_for_string=True,))


def modify_cert(conf):
    """This function modifies each of the certs
       (ca cert, client cert and client key)
       as a single line string to make it compatible with Grafana.
    """
    fpd = open(conf["trustFile"], 'r')
    lines = fpd.readlines()
    tls_ca_cert = "\\n".join([line.strip() for line in lines])
    fpd = open(conf["certFile"], 'r')
    lines = fpd.readlines()
    tls_client_cert = "\\n".join([line.strip() for line in lines])
    fpd = open(conf["keyFile"], 'r')
    lines = fpd.readlines()
    tls_client_key = "\\n".join([line.strip() for line in lines])

    cert = {}
    cert['tls_ca_cert'] = tls_ca_cert
    cert['tls_client_cert'] = tls_client_cert
    cert['tls_client_key'] = tls_client_key

    return cert


def generate_prod_datasource_file(db_config, conf):
    """This function generates the grafana datasource config for PROD mode
    """

    cert_dict = modify_cert(conf)
    db_tags = ["user", "password", "database"]
    tls_config = {"tlsAuth": "true",
                  "tlsAuthWithCACert": "true",
                  "tlsCACert": cert_dict['tls_ca_cert'],
                  "tlsClientCert": cert_dict['tls_client_cert'],
                  "tlsClientKey": cert_dict['tls_client_key']}

    with open('./Grafana/datasource_sample.yml', 'r') as fin:
        with open(TEMP_DS, "w+") as fout:
            for line in fin.readlines():
                not_done = True
                for tag in db_tags:
                    if tag + ':' in line:
                        line = line.replace('""', db_config[tag])
                        fout.write(line)
                        not_done = False

                for key, value in tls_config.items():
                    if key + ':' in line:
                        if key in ("tlsAuth", "tlsAuthWithCACert"):
                            line = line.replace('false', value)
                        else:
                            line = line.replace('"..."', '"' + value + '"')
                        fout.write(line)
                        not_done = False

                if "url:" in line:
                    line = line.replace('http://$INFLUX_SERVER:8086',
                                        'https://$INFLUX_SERVER:8086')
                    fout.write(line)
                    not_done = False

                if not_done:
                    fout.write(line)


def generate_prod_ini_file():
    """This function generates the grafana.ini config for PROD mode
    """
    connection_config = {"protocol": "https",
                         "cert_file": CERT_FILE,
                         "cert_key": KEY_FILE,
                         "http_addr": os.environ['GRAFANA_SERVER']}

    with open('./Grafana/grafana_template.ini', 'r') as fin:
        with open(CONF_FILE, "w+") as fout:
            for line in fin.readlines():
                not_done = True
                for key, value in connection_config.items():
                    if ";" + key + " =" in line:
                        if key == "protocol":
                            line = line.replace(';' + key + ' = http',
                                                key + ' = ' + value)
                            fout.write(line)
                            not_done = False
                        elif key == "http_addr":
                            if os.environ['GRAFANA_SERVER']:
                                value = os.environ['GRAFANA_SERVER']
                            line = line.replace(';' + key + ' =',
                                                key + ' = ' + value)
                            fout.write(line)
                            not_done = False
                        else:
                            line = line.replace(';' + key + ' =',
                                                key + ' = ' + value)
                            fout.write(line)
                            not_done = False

                if not_done:
                    fout.write(line)


def generate_dev_datasource_file(db_config):
    """This function generates the grafana datasource config for DEV mode
    """
    with open('./Grafana/datasource_sample.yml', 'r') as fin:
        with open(TEMP_DS, "w+") as fout:
            for line in fin.readlines():
                if "user:" in line:
                    line = line.replace('""', db_config['user'])
                    fout.write(line)
                elif "password:" in line:
                    line = line.replace('""', db_config['password'])
                    fout.write(line)
                elif "database:" in line:
                    line = line.replace('""', db_config['database'])
                    fout.write(line)
                else:
                    fout.write(line)


def generate_dev_ini_file():
    """This function generates the grafana.ini config for DEV mode
    """
    with open('./Grafana/grafana_template.ini', 'r') as fin:
        with open(CONF_FILE, "w+") as fout:
            for line in fin.readlines():
                if ";http_addr =" in line:
                    host = os.environ['GRAFANA_SERVER']
                    line = line.replace(';http_addr =', 'http_addr = ' + host)
                    fout.write(line)
                else:
                    fout.write(line)


def read_config(app_cfg):
    """This function reads the InfluxDBConnector config
       from etcd to fetch the InfluxDB credentials
    """
    influx_uname = os.environ["INFLUXDB_USERNAME"]
    influx_pwd = os.environ["INFLUXDB_PASSWORD"]
    dbname = app_cfg["influxdb"]["dbname"]

    db_conf = {}
    db_conf['user'] = influx_uname
    db_conf['password'] = influx_pwd
    db_conf['database'] = dbname

    return db_conf


def copy_config_files():
    """This function copies the modified grafana config files
    """
    dashboard_dir = "{}/conf/provisioning/dashboards".format(GRAFANA_DIR)
    shutil.copy('./Grafana/dashboard_sample.yml',
                dashboard_dir + '/dashboard_sample.yml')
    shutil.copy('./Grafana/dashboard.json',
                dashboard_dir + '/dashboard.json')
    copy_tree('/var/lib/grafana/plugins',
              '/tmp/grafana/lib/grafana/plugins')


def get_grafana_config(app_cfg):
    """This function reads the certificates from etcd
       and writes it to respective files.
    """
    # Set path to certs here
    ca_cert = app_cfg["ca_cert"]
    server_cert = app_cfg["server_cert"]
    server_key = app_cfg["server_key"]

    with open(CA_FILE, 'w') as fpd:
        fpd.write(ca_cert)
    os.chmod(CA_FILE, 0o400)

    with open(CERT_FILE, 'w') as fpd:
        fpd.write(server_cert)
    os.chmod(CERT_FILE, 0o400)

    with open(KEY_FILE, 'w') as fpd:
        fpd.write(server_key)
    os.chmod(KEY_FILE, 0o400)

    eii_cert_path = {}
    eii_cert_path['trustFile'] = CA_FILE
    eii_cert_path['certFile'] = CERT_FILE
    eii_cert_path['keyFile'] = KEY_FILE

    return eii_cert_path


def modify_multi_instance_dashboard():
    """To modify dashboard in case of multiple
       video streams
    """
    js = None
    with open('./Grafana/dashboard.json', "rb") as f:
        js = json.loads(f.read())
        default_panel = js['panels'][1]
        default_url = js['panels'][1]['url']
        default_title = js['panels'][1]['title']
        del js['panels'][1]
        for i in range(0, len(topics_list)):
            multi_instance_panel = copy.deepcopy(default_panel)
            multi_instance_panel['url'] = \
                default_url.replace(topics_list[0], topics_list[i])
            multi_instance_panel['url'] = \
                multi_instance_panel['url'].replace('127.0.0.1',
                                                    os.environ['HOST_IP'])
            if not dev_mode:
                multi_instance_panel['url'] = \
                    multi_instance_panel['url'].replace('http', 'https')
            if dev_mode:
                multi_instance_panel['url'] = \
                    multi_instance_panel['url'].replace(str(app_cfg['port']),
                                                        str(app_cfg['dev_port']))
            multi_instance_panel['title'] = \
                default_title.replace(topics_list[0], topics_list[i])
            multi_instance_panel['id'] = \
                multi_instance_panel['id'] + i
            multi_instance_panel['gridPos']['y'] = \
                int(multi_instance_panel['gridPos']['y'])*(i+1)
            js['panels'].append(multi_instance_panel)
        for i in range(1, len(topics_list)+1):
            port = js['panels'][i]['url'].split(":")[-1].split("/")[0]
            new_port = int(port) + (math.ceil(i/6) - 1)
            js['panels'][i]['url'] = js['panels'][i]['url'].replace(port,
                                                                    str(new_port))
    with open('./Grafana/dashboard.json', "w") as f:
        json.dump(js, f, ensure_ascii=False, indent=4)


def msg_bus_subscriber(topic_name, logger, json_config):
    """msg_bus_subscriber is the ZeroMQ callback to
    subscribe to classified results
    """
    visualizer = Visualizer(queue_dict, logger,
                            labels=json_config["labels"],
                            draw_results=json_config["draw_results"])

    for topic_config in topic_config_list:

        topic, msgbus_cfg = topic_config

        if topic_name == topic:
            callback_thread = threading.Thread(target=visualizer.callback,
                                               args=(msgbus_cfg, topic, ))
            callback_thread.start()
            break


def get_blank_image(text):
    """Get Blank Images
    """
    blank_image_shape = (130, 200, 3)
    blank_image = np.zeros(blank_image_shape, dtype=np.uint8)
    cv2.putText(blank_image, text, TEXTPOSITION,
                TEXTFONT, 1.5, TEXTCOLOR, 2, cv2.LINE_AA)
    _, jpeg = cv2.imencode('.jpg', blank_image)
    final_image = jpeg.tobytes()
    return final_image


def get_image_data(topic_name):
    """Get the Images from Zmq
    """
    dev_mode = ctx.is_dev_mode()

    logger = configure_logging(os.environ['PY_LOG_LEVEL'].upper(),
                               __name__, dev_mode)
    try:
        final_image = get_blank_image(TEXT)
        msg_bus_subscriber(topic_name, logger, app_cfg)
        while True:
            if topic_name in queue_dict.keys():
                if not queue_dict[topic_name].empty():
                    frame = queue_dict[topic_name].get()
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    del frame
                    final_image = jpeg.tobytes()
                    del jpeg
            else:
                raise Exception(f"Topic: {topic_name} doesn't exist")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + final_image +
                   b'\r\n\r\n')
    except KeyboardInterrupt:
        log.exception('Quitting due to keyboard interrupt...')
    except Exception:
        log.exception('Error during execution:')


def set_header_tags(response):
    """Local function to set secure response tags"""
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=1024000;\
                                                    includeSubDomains'
    return response


@APP.route('/')
def index():
    """Video streaming home page."""

    response = APP.make_response(render_template('index.html',
                                                 nonce=NONCE))
    return set_header_tags(response)


@APP.route('/topics', methods=['GET'])
def return_topics():
    """Returns topics list over http
    """
    return Response(str(topics_list))


@APP.route('/<topic_name>', methods=['GET'])
def render_image(topic_name):
    """Renders images over http
    """
    if topic_name in topics_list:
        return Response(get_image_data(topic_name),
                        mimetype='multipart/x-mixed-replace;\
                                  boundary=frame')

    return Response("Invalid Request")


def flask_runner(context, port):
    """Method to run flask server
    """

    # Start a flask server instance
    APP.run(host='0.0.0.0', port=port,  # nosec
            debug=False, threaded=True,
            ssl_context=context)


def main():
    """Main method for grafana
    """

    if not dev_mode:
        eii_cert_path = get_grafana_config(app_cfg)

    log.info("=============== STARTING grafana ===============")
    db_config = read_config(app_cfg)

    if not dev_mode:
        log.info("generating prod mode config files for grafana")
        generate_prod_datasource_file(db_config, eii_cert_path)
        generate_prod_ini_file()
    else:
        log.info("generating dev mode config files for grafana")
        generate_dev_datasource_file(db_config)
        generate_dev_ini_file()

    # Multi instace variables
    context, port = None, None
    num_of_subs = 0
    threads = []

    try:
        # Initializing subscriber for multiple streams
        num_of_subs = ctx.get_num_subscribers()
        if num_of_subs > 0:
            for index in range(0, num_of_subs):
                sub_ctx = ctx.get_subscriber_by_index(index)
                msgbus_config = sub_ctx.get_msgbus_config()
                topic = sub_ctx.get_topics()[0]
                # Adding topic & msgbus_config to
                # topic_config tuple
                topic_config = (topic, msgbus_config)
                topic_config_list.append(topic_config)
                topics_list.append(topic)
                queue_dict[topic] = queue.Queue(maxsize=FRAME_QUEUE_SIZE)
            modify_multi_instance_dashboard()
    except Exception as e:
        log.warn(f"No subscriber instances found {e}")

    copy_config_files()

    if not dev_mode:
        APP.secret_key = os.urandom(24)
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # For Secure Session Cookie
        APP.config.update(SESSION_COOKIE_SECURE=True,
                          SESSION_COOKIE_SAMESITE='Lax')

        server_cert = app_cfg["server_cert"]
        server_key = app_cfg["server_key"]

        # Since Python SSL Load Cert Chain Method is not having option to load
        # Cert from Variable. So for now we are going below method
        server_cert_temp = tempfile.NamedTemporaryFile()
        server_key_temp = tempfile.NamedTemporaryFile()

        server_cert_temp.write(bytes(server_cert, "utf-8"))
        server_cert_temp.seek(0)

        server_key_temp.write(bytes(server_key, "utf-8"))
        server_key_temp.seek(0)

        context.load_cert_chain(server_cert_temp.name, server_key_temp.name)
        server_cert_temp.close()
        server_key_temp.close()

    # All browser security limitations retrict flask from serving
    # more than 6 requests
    # Hence, running a flask server instance for every 6 streams
    if dev_mode:
        port = app_cfg['dev_port']
    else:
        port = app_cfg['port']

    for i in range(0, (math.ceil(num_of_subs/6))):
        port = port + i
        thread = threading.Thread(target=flask_runner,
                                  args=(context,
                                        port, ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
