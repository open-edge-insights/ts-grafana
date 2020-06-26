#!/bin/bash

# Copyright (c) 2020 Intel Corporation.

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

# to debug uncomment below line
# set -x

: "${GRAFANA_DATA_PATH:=/tmp/grafana/lib/grafana}"
: "${GRAFANA_LOGS_PATH:=/tmp/grfana/log/grafana}"
: "${GRAFANA_PLUGINS_PATH:=/tmp/grafana/lib/grafana/plugins}"

echo "Copying the grafana configurations to /tmp"
cp -r /usr/share/grafana /tmp/

echo "Grafana enabled"
python3.6 ./Grafana/modify_grafana_files.py

if [ $? -eq 0 ]; then
    echo "Grafana configuration files modified successfully"
    exec grafana-server  \
    --homepath=/tmp/grafana/                  \
    --config=/tmp/grafana/grafana.ini         \
    cfg:default.paths.data="$GRAFANA_DATA_PATH"   \
    cfg:default.paths.logs="$GRAFANA_LOGS_PATH"   \
    cfg:default.paths.plugins="$GRAFANA_PLUGINS_PATH"
else
    echo "Failed to modify Grafana configuration files. Exiting!!!"
fi
