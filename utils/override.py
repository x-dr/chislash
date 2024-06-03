#coding: utf-8
import yaml
import sys
import os
from collections.abc import Mapping
ext_template = r"""
redir-port: 0
port: %s
socks-port: %s
tproxy-port: %s
mixed-port: %s
bind-address: '*'
allow-lan: true
log-level: %s  # 日志等级 silent/error/warning/info/debug
ipv6: %s
#  find-process-mode has 3 values:always, strict, off
#  - always, 开启，强制匹配所有进程
#  - strict, 默认，由 mihomo 判断是否开启
#  - off, 不匹配进程，推荐在路由器上使用此模式
find-process-mode: strict
mode: rule

#自定义 geodata url
geox-url:
  geoip: "https://kkgithub.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.dat"
  geosite: "https://kkgithub.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat"
  mmdb: "https://kkgithub.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb"

geo-auto-update: false # 是否自动更新 geodata
geo-update-interval: 24 # 更新间隔，单位：小时


profile: # 存储 select 选择记录
  store-selected: true
  # 持久化 fake-ip
  store-fake-ip: true

# 嗅探域名 可选配置
sniffer:
  enable: true
  force-dns-mapping: true
  parse-pure-ip: true
  override-destination: false
  sniff:
    HTTP:
      ports: [80, 8080-8880]
      override-destination: true
    TLS:
      ports: [443, 8443]
    QUIC:
      ports: [443, 8443]
  force-domain:
    - +.v2ex.com
  skip-domain:
    - Mijia Cloud

#dns 服务配置
dns:
  cache-algorithm: arc
  enable: true # 是否启用 DNS 服务
  listen: 0.0.0.0:1053 # 监听地址
  ipv6: false # false 将返回 AAAA 的空结果
  enhanced-mode: redir-host
  use-hosts: true # 查询 hosts
  # 用于解析 nameserver，fallback 以及其他DNS服务器配置的，DNS 服务域名
  # 只能使用纯 IP 地址，可使用加密 DNS
  default-nameserver:
    - 223.5.5.5
    - 119.29.29.29
    - 8.8.8.8
    - tls://1.12.12.12:853
    - tls://223.5.5.5:853
    - system # append DNS server from system configuration. If not found, it would print an error log and skip.
  
  # DNS主要域名配置
  # 支持 UDP，TCP，DoT，DoH，DoQ
  # 这部分为主要 DNS 配置，影响所有直连，确保使用对大陆解析精准的 DNS 服务器
  nameserver:
    - dhcp://en0 # dns from dhcp
    - tls://223.5.5.5:853 # DNS over TLS
    - https://doh.pub/dns-query
    - https://dns.alidns.com/dns-query

  # 当配置 fallback 时，会查询 nameserver 中返回的 IP 是否为 CN，非必要配置
  # 当不是 CN，则使用 fallback 中的 DNS 查询结果
  # 确保配置 fallback 时能够正常查询
  fallback:
    - dhcp://en0 # dns from dhcp
    - 'tls://1.1.1.1:853'
    - 'tcp://1.1.1.1:53'
    - 'tcp://208.67.222.222:443'
    - 'tls://dns.google'
  # 配置查询域名使用的 DNS 服务器
  nameserver-policy:
    #   'www.baidu.com': '114.114.114.114'
    #   '+.internal.crop.com': '10.0.0.1'
    "geosite:cn,private,apple":
      - https://doh.pub/dns-query
      - https://dns.alidns.com/dns-query
    "geosite:category-ads-all": rcode://success
    "www.baidu.com,+.google.cn": [223.5.5.5, https://dns.alidns.com/dns-query]
    ## global，dns 为 rule-providers 中的名为 global 和 dns 规则订阅，
    ## 且 behavior 必须为 domain/classical，当为 classical 时仅会生效域名类规则
    # "rule-set:global,dns": 8.8.8.8
"""

def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def override(user_config, required_config, ext):
    user = yaml.load(open(user_config, 'r', encoding="utf-8").read(), Loader=yaml.FullLoader)
    for dnskey in ['default-nameserver', 'nameserver', 'fallback']:
      if 'dns' in user and dnskey in user['dns'] and user['dns'][dnskey]:
        ed = ext['dns']
        del ed[dnskey]
        ext['dns'] = ed
    deep_update(user, ext)
    if required_config:
      must = yaml.load(open(required_config, 'r', encoding="utf-8").read(), Loader=yaml.FullLoader)
      deep_update(user, must)
    user_file = open(user_config, 'w', encoding="utf-8")
    yaml.dump(user, user_file)
    user_file.close()

_,user_config,required_config,port,socks_port,tproxy_port,mixed_port,log_level,ipv6_proxy = sys.argv
override(
  user_config, required_config,
  yaml.load(ext_template%(
    port,
    socks_port,
    tproxy_port,
    mixed_port,
    log_level,
    ipv6_proxy=="1",
    ), Loader=yaml.FullLoader))

