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

import os
import shutil
import yaml
import json
from distutils.util import strtobool
from libs.ConfigManager import ConfigManager
from util.log import configure_logging, LOG_LEVELS
from util.util import Util

def generate_prod_config_files(user_name, password, dbname):

    f = open('/run/secrets/ca_etcd', 'r')
    lines = f.readlines()
    tlsCACert = "\\n".join([line.strip() for line in lines])
    f = open('/run/secrets/etcd_Grafana_cert', 'r')
    lines = f.readlines()
    tlsClientCert = "\\n".join([line.strip() for line in lines])
    f = open('/run/secrets/etcd_Grafana_key', 'r')
    lines = f.readlines()
    tlsClientKey = "\\n".join([line.strip() for line in lines])


    with open('./Grafana/datasource_sample.yml', 'r') as fin:
        with open("./Grafana/datasource.yml", "w+") as fout:
            for line in fin.readlines():
                if "url:" in line:
                    line=line.replace('http://localhost:8086', 'https://localhost:8086')
                    fout.write(line)
                elif "user:" in line:
                    line=line.replace('""', user_name)
                    fout.write(line)
                elif "password:" in line:
                    line=line.replace('""', password)
                    fout.write(line)
                elif "database:" in line:
                    line=line.replace('""', dbname)
                    fout.write(line)
                elif "tlsAuth:" in line:
                    line=line.replace('false', 'true')
                    fout.write(line)
                elif "tlsAuthWithCACert:" in line:
                    line=line.replace('false', 'true')
                    fout.write(line)
                elif "tlsCACert:" in line:
                    line=line.replace('"..."', '"' + tlsCACert + '"')
                    fout.write(line)
                elif "tlsClientCert:" in line:
                    line=line.replace('"..."', '"' + tlsClientCert + '"')
                    fout.write(line)
                elif "tlsClientKey:" in line:
                    line=line.replace('"..."', '"' + tlsClientKey + '"')
                    fout.write(line)
                else: 
                    fout.write(line)

    with open('./Grafana/grafana_template.ini', 'r') as fin:
        with open("./Grafana/grafana.ini", "w+") as fout:
            cert_file_updated = False
            for line in fin.readlines():
                if ";protocol =" in line:
                    line=line.replace(';protocol = http','protocol = https')
                    fout.write(line)
                elif ";cert_file =" in line and not cert_file_updated:
                    line=line.replace(';cert_file =','cert_file = /etc/grafana/server_cert.pem')
                    fout.write(line)
                    cert_file_updated = True
                elif ";cert_key =" in line:
                    line=line.replace(';cert_key =','cert_key = /etc/grafana/server_key.pem')
                    fout.write(line)
                else: 
                    fout.write(line)           
        
    
def generate_dev_config_files(user_name, password, dbname):
    with open('./Grafana/datasource_sample.yml', 'r') as fin:
        with open("./Grafana/datasource.yml", "w+") as fout:
            for line in fin.readlines():
                if "user:" in line:
                    line=line.replace('""', user_name)
                    fout.write(line)
                elif "password:" in line:
                    line=line.replace('""', password)
                    fout.write(line)
                elif "database:" in line:
                    line=line.replace('""', dbname)
                    fout.write(line)
                else:
                    fout.write(line)


def read_config (client, dev_mode):
    influx_app_name = os.environ["InfluxDbAppName"]
    config_key_path = "config"
    configfile = client.GetConfig("/{0}/{1}".format(
        influx_app_name, config_key_path))
    config = json.loads(configfile)
    user_name = config["influxdb"]["username"]
    password = config["influxdb"]["password"]
    dbname = config["influxdb"]["dbname"]

    if not dev_mode :
        log.info("generating prod mode config files for grafana")
        generate_prod_config_files(user_name, password, dbname)
    else :
        log.info("generating dev mode config files for grafana")
        generate_dev_config_files(user_name, password, dbname)

def copy_config_files(dev_mode):

    Destination_folder_for_dashboards = '/usr/share/grafana/conf/provisioning/dashboards'
    Destination_folder_for_datasource = '/usr/share/grafana/conf/provisioning/datasources'
    if dev_mode:
        shutil.copy('./Grafana/dashboard_sample.yml', Destination_folder_for_dashboards + '/dashboard_sample.yml')
        shutil.copy('./Grafana/dashboard.json', Destination_folder_for_dashboards + '/dashboard.json')
        shutil.copy('./Grafana/datasource.yml', Destination_folder_for_datasource + '/datasource.yml')
        shutil.copy('./Grafana/grafana_template.ini','/etc/grafana/grafana.ini')
    else:
        shutil.copy('./Grafana/datasource.yml', Destination_folder_for_datasource + '/datasource.yml')
        shutil.copy('./Grafana/dashboard_sample.yml', Destination_folder_for_dashboards + '/dashboard_sample.yml')
        shutil.copy('./Grafana/dashboard.json', Destination_folder_for_dashboards + '/dashboard.json')
        shutil.copy('./Grafana/grafana.ini','/etc/grafana/grafana.ini')


def get_grafana_config():
    app_name = os.environ["AppName"]
    conf = Util.get_crypto_dict(app_name)
    cfg_mgr = ConfigManager()
    config_client = cfg_mgr.get_config_client("etcd", conf)
    server_cert = config_client.GetConfig("/" + app_name + "/server_cert")
    server_key = config_client.GetConfig("/" + app_name + "/server_key")

    with open('server_cert.pem', 'w') as f:
        f.write(server_cert)

    with open('server_key.pem', 'w') as f:
        f.write(server_key)

    shutil.copy('server_cert.pem','/etc/grafana/server_cert.pem')
    shutil.copy('server_key.pem','/etc/grafana/server_key.pem')

if __name__ == "__main__":
    
    dev_mode = strtobool(os.environ['DEV_MODE'])
    influx_app_name = os.environ["InfluxDbAppName"]
    conf = Util.get_crypto_dict(influx_app_name)
    cfg_mgr = ConfigManager()
    config_client = cfg_mgr.get_config_client("etcd", conf)

    if not dev_mode:
        get_grafana_config()

    log = configure_logging(os.environ['PY_LOG_LEVEL'].upper(),__name__,dev_mode)
    log.info("=============== STARTING grafana ===============")
    read_config(config_client, dev_mode)
    copy_config_files(dev_mode)
