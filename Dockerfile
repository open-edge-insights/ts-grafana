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

#Dockerfile for Grafana

ARG EII_VERSION
ARG OPENVINO_IMAGE
# FROM ${OPENVINO_IMAGE} AS openvino
FROM ia_eiibase:$EII_VERSION as base
FROM ia_common:$EII_VERSION as common

FROM base as builder

WORKDIR /app

ARG CMAKE_INSTALL_PREFIX

# Install libzmq
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4.tar.gz -O zeromq.tar.gz && \
    tar xf zeromq.tar.gz && \
    cd zeromq-4.3.4 && \
    ./configure --prefix=${CMAKE_INSTALL_PREFIX} && \
    make install

# Install cjson
RUN rm -rf deps && \
    mkdir -p deps && \
    cd deps && \
    wget -q --show-progress https://github.com/DaveGamble/cJSON/archive/v1.7.12.tar.gz -O cjson.tar.gz && \
    tar xf cjson.tar.gz && \
    cd cJSON-1.7.12 && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_INCLUDEDIR=${CMAKE_INSTALL_PREFIX}/include -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} .. && \
    make install

COPY --from=common ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib

COPY requirements.txt .

RUN pip3 install --user -r requirements.txt

FROM ${OPENVINO_IMAGE} as runtime

LABEL description="Grafana image"

WORKDIR /app

USER root
ARG GRAFANA_VERSION
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://dl.grafana.com/oss/release/grafana-$GRAFANA_VERSION.linux-amd64.tar.gz && \
    tar -zxvf grafana-$GRAFANA_VERSION.linux-amd64.tar.gz

ENV GRAFANA_VERSION ${GRAFANA_VERSION}
ENV PATH $PATH:/app/grafana-$GRAFANA_VERSION/bin
RUN grafana-cli --pluginsDir "/var/lib/grafana/plugins" plugins install ryantxu-ajax-panel

RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip wget && \
    mkdir static && \
    wget -q --show-progress https://github.com/twbs/bootstrap/releases/download/v4.0.0/bootstrap-4.0.0-dist.zip && \
    unzip bootstrap-4.0.0-dist.zip -d static && \
    rm -rf bootstrap-4.0.0-dist.zip && \
    wget -q --show-progress https://code.jquery.com/jquery-3.4.1.min.js && \
    mv jquery-3.4.1.min.js static/js/jquery.min.js && \
    rm -rf /var/lib/apt/lists/*

COPY . ./Grafana

ARG EII_UID
ARG EII_USER_NAME
RUN groupadd $EII_USER_NAME -g $EII_UID && \
    useradd -r -u $EII_UID -g $EII_USER_NAME $EII_USER_NAME

ARG CMAKE_INSTALL_PREFIX
ENV PYTHONPATH $PYTHONPATH:/app/.local/lib/python3.8/site-packages:/app:/opt/intel/openvino/python/python3
COPY --from=builder ${CMAKE_INSTALL_PREFIX}/lib ${CMAKE_INSTALL_PREFIX}/lib
COPY --from=common /eii/common/util util
COPY --from=common /root/.local/lib .local/lib
COPY --from=builder /root/.local/lib .local/lib

RUN mkdir /tmp/grafana && \
    chown -R ${EII_UID}:${EII_UID} /tmp/ ./Grafana/ ${CMAKE_INSTALL_PREFIX} && \
    chmod -R 760 /tmp/ ./Grafana/ ${CMAKE_INSTALL_PREFIX}

RUN apt-get remove --purge -y unzip
RUN chown -R ${EII_UID} .local/lib/python3.8

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:${CMAKE_INSTALL_PREFIX}/lib
ENV PATH $PATH:/app/.local/bin
USER $EII_USER_NAME

HEALTHCHECK NONE

ENTRYPOINT ["./Grafana/run.sh"]
