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
from distutils.util import strtobool
import cfgmgr.config_manager as cfg
from util.log import configure_logging

TMP_DIR = tempfile.gettempdir()
GRAFANA_DIR = os.path.join(TMP_DIR, "grafana")
CERT_FILE = "{}/server_cert.pem".format(GRAFANA_DIR)
KEY_FILE = "{}/server_key.pem".format(GRAFANA_DIR)
CA_FILE = "{}/ca_cert.pem".format(GRAFANA_DIR)
CONF_FILE = "{}/grafana.ini".format(GRAFANA_DIR)
TEMP_DS = "{}/conf/provisioning/datasources/datasource.yml".format(GRAFANA_DIR)


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
    user_name = app_cfg["influxdb"]["username"]
    password = app_cfg["influxdb"]["password"]
    dbname = app_cfg["influxdb"]["dbname"]

    db_conf = {}
    db_conf['user'] = user_name
    db_conf['password'] = password
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

    with open(CERT_FILE, 'w') as fpd:
        fpd.write(server_cert)

    with open(KEY_FILE, 'w') as fpd:
        fpd.write(server_key)

    eii_cert_path = {}
    eii_cert_path['trustFile'] = CA_FILE
    eii_cert_path['certFile'] = CERT_FILE
    eii_cert_path['keyFile'] = KEY_FILE

    return eii_cert_path


def main():
    """Main method for grafana
    """
    ctx = cfg.ConfigMgr()
    app_cfg = ctx.get_app_config()
    dev_mode = ctx.is_dev_mode()

    if not dev_mode:
        eii_cert_path = get_grafana_config(app_cfg)

    log = configure_logging(os.environ['PY_LOG_LEVEL'].upper(), __name__,
                            dev_mode)
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

    copy_config_files()


if __name__ == "__main__":
    main()
