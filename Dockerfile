FROM ubuntu:jammy

# 设置时区为 Asia/Shanghai
ENV TZ=Asia/Shanghai
# 设置环境变量，使debconf使用非交互式前端
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y wget xz-utils iproute2 iptables supervisor \
        curl python3 python3-yaml kmod python3-pip tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm /bin/sh && ln -s /bin/bash /bin/sh \
    && mv -v /usr/sbin/ip6tables /usr/sbin/ip6tables--DISABLED-$(date +"%Y-%m-%d--%H-%M") \
    && cp -v /usr/sbin/ip6tables-nft /usr/sbin/ip6tables \
    && mv -v /usr/sbin/iptables /usr/sbin/iptables--DISABLED-$(date +"%Y-%m-%d--%H-%M") \
    && cp -v /usr/sbin/iptables-nft /usr/sbin/iptables \
    && mkdir -p /default/clash/dashboard \
    && mkdir -p /default/clash/metacubexd 


#  设置时区
RUN echo $TZ > /etc/timezone \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime



COPY Yacd-meta /default/clash/dashboard
COPY metacubexd   /default/clash/metacubexd
COPY Country.mmdb /default/clash/Country.mmdb


ARG CLASHMETAVER=v1.18.1
ARG SCVER=v0.92

RUN echo 'detect arch ...' \
    && SC_ARCH='unknown' && ARCH='unknown' \
    &&  if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64 ; export SC_ARCH='linux64'; else if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64 ; export SC_ARCH='aarch64'; fi fi  \
    && echo "$ARCH" \
    && echo 'install  Clash Meta  ...' \
    && wget https://github.com/MetaCubeX/mihomo/releases/download/$CLASHMETAVER/mihomo-linux-$ARCH-$CLASHMETAVER.gz \
    && gunzip mihomo-linux-$ARCH-$CLASHMETAVER.gz \
    && mv mihomo-linux-$ARCH-$CLASHMETAVER /usr/bin/clash \
    && chmod 774 /usr/bin/clash \
    && cp /usr/bin/clash /usr/bin/clash-meta \

    && echo 'install  subconverter ...' \
    && wget https://github.com/x-dr/subconverter/releases/download/$SCVER/subconverter_$SC_ARCH.tar.gz \
    && gunzip subconverter_$SC_ARCH.tar.gz && tar xvf subconverter_$SC_ARCH.tar && rm subconverter_$SC_ARCH.tar \
    && mv subconverter /default/ \


    && wget https://github.com/ACL4SSR/ACL4SSR/archive/refs/heads/master.tar.gz \
    && gunzip master.tar.gz && tar xvf master.tar && rm master.tar \
    && mkdir /default/exports && mv ACL4SSR-master /default/exports/ACL4SSR \
    && chmod -R a+r /default/


ENV ENABLE_CLASH=1
ENV REQUIRED_CONFIG=""
ENV CLASH_HTTP_PORT=7890
ENV CLASH_SOCKS_PORT=7891
ENV CLASH_TPROXY_PORT=7892
ENV CLASH_MIXED_PORT=7893
ENV DASH_PORT=8080
ENV DASH_PATH="/etc/clash/metacubexd"
ENV IP_ROUTE=1
ENV UDP_PROXY=1
ENV IPV6_PROXY=1
ENV PROXY_FWMARK=0x162
ENV PROXY_ROUTE_TABLE=0x162
ENV LOG_LEVEL="info"
ENV SECRET=""
ENV ENABLE_SUBCONV=1
ENV SUBCONV_URL="http://127.0.0.1:25500/sub"
ENV SUBSCR_URLS=""
ENV SUBSCR_EXPR=6000
ENV REMOTE_CONV_RULE="http://127.0.0.1:8091/ACL4SSR/Clash/config/ACL4SSR_Online_Full.ini"
ENV EXPORT_DIR_PORT=8091
ENV EXPORT_DIR_BIND='0.0.0.0'
ENV NO_ENGLISH=true
ENV PREMIUM=true
EXPOSE $CLASH_HTTP_PORT $CLASH_SOCKS_PORT $CLASH_TPROXY_PORT $CLASH_MIXED_PORT $DASH_PORT $SUBCONV_PORT
VOLUME /etc/clash
COPY root/ /myroot
COPY root/entrypoint.sh /entrypoint.sh
COPY utils /default/clash/utils
RUN useradd -g root -s /bin/bash -u 1086 -m clash
ENTRYPOINT [ "/entrypoint.sh" ]
