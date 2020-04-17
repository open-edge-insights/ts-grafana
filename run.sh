#!/bin/bash 

# to debug uncomment below line
# set -x

: "${GF_PATHS_DATA:=/var/lib/grafana}"
: "${GF_PATHS_LOGS:=/var/log/grafana}"
: "${GF_PATHS_PLUGINS:=/var/lib/grafana/plugins}"


echo "Grafana enabled"
python3.6 ./Grafana/modify_grafana_files.py

if [ $? -eq 0 ]; then
    exec grafana-server  \
    --homepath=/usr/share/grafana             \
    --config=/etc/grafana/grafana.ini         \
    cfg:default.paths.data="$GF_PATHS_DATA"   \
    cfg:default.paths.logs="$GF_PATHS_LOGS"   \
    cfg:default.paths.plugins="$GF_PATHS_PLUGINS"
else
    echo "modify_grafana_files.py failed to execute. Exiting!!!"
fi
