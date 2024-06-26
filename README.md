# chislash
- 开箱即用的clash透明网关
- 也可作为[纯订阅转换服务](#其它场景)使用
## 警告
- 十分**不建议**在云服务器(甲骨文,AWS...)上使用透明代理特性(IP_ROUTE=1)！ 任何意外情况都可能导致你的服务器失联
- 如果依然要使用,请关闭透明代理特性,作为HTTP/SOCKS5代理服务器使用; 参考[非透明代理](#其它场景)
## 环境检查
- 检查是否支持TProxy(支持TProxy, 才能使用透明代理)
```
lsmod | grep xt_TPROXY
```
- 如果没有返回,则需要加载
```
modprobe xt_TPROXY
``` 
- 如果没有报错,设置自动加载xt_TPROXY
```
sudo bash -c "echo 'xt_TPROXY' >/etc/modules-load.d/TPROXY.conf"
```
## 快速上手
- 将Linux服务器(树莓派,工控机,闲置电脑)作为透明代理
- 一行搞定
```bash
sudo docker run --name chislash \
    --network="host" \
    --privileged \
    --rm -it \
    -e SUBSCR_URLS=<(自带配置可不填)节点订阅链接或代理节点的分享链接, 多个用'|'分隔> \
    -v $HOME/.config/chislash:/etc/clash \
    -v /dev:/dev \
    -v /lib/modules:/lib/modules \
    gindex/chislash:latest
```
- 成功启动, 输出如下图的日志
![quickstart](https://github.com/gindex/chislash/raw/master/images/quickstart.png)
- 如果失败, 请检查
  - 订阅链接(SUBSCR_URLS)是否能正常访问. 如果不能, 请联系供应商
  - 规则链接(REMOTE_CONV_RULE)是否能正常访问. 可添加 *-e REMOTE_CONV_RULE=""* 到命令中重试
- 调试通过后, 作为后台服务: 将 *--rm -it* 改为 *--restart unless-stopped -d*
- 此时Linux服务器本身已经被代理接管, 将其设置为网关后, 其它机器也可获得透明代理
- 控制台
  - **http://< 服务器IP >:8080/ui**  为clash的WebUI, 用于切换节点
  - **http://< 服务器IP >:25500** 为subconverter后端服务地址, 用于节点订阅转换
## 其它场景
- 非透明代理
```bash
sudo docker run --name chislash \
    --network="host" \
    --rm -it \
    -e IP_ROUTE=0 \
    -e SUBSCR_URLS=<(自带配置可不填)节点订阅链接或代理节点的分享链接, 多个用'|'分隔> \
    -v $HOME/.config/chislash:/etc/clash \
    gindex/chislash:latest
```
- 关闭IPv6代理: *-e IPV6_PROXY=0*
- 关闭UDP代理: *-e UDP_PROXY=0*
- 纯订阅转换服务(subconverter)
```bash
sudo docker run --name chislash \
    --rm -it \
    -e ENABLE_CLASH=0 \
    -p 25500:25500 \
    -p 8091:8091 \
    -e SUBSCR_URLS=<(可不填, 填写后启动会更新/etc/clash/config.yaml)> \
    -v $HOME/.config/chislash:/etc/clash \
    gindex/chislash:latest
```
  - 转换服务: *http://127.0.0.1:25500/sub*
  - 转换规则: *http://127.0.0.1:8091/ACL4SSR/Clash/config/* 
## 进阶使用


- 一些细节
  - 透明代理: 容器自动映射路由表, 劫持本地DNS流量实现本地透明代理; 亦可作为网关使用, 需要将网关和DNS指定为服务器IP
  - 配置文件: 请注意备份配置文件, 容器会修改部分用户配置来统一端口和部分高级配置, utils/override.py中定义了本镜像修改用户配置的方式
- docker-compose
```yaml
version: "3.4"
services:
  chislash:
    image: gindex/chislash
    container_name: chislash
    # 以下样例中的 "/etc/clash/" 代表容器内目录
    environment:
      - TZ=Asia/Shanghai       # optional
      # - REQUIRED_CONFIG=<path to required.yaml> # optional 
      # REQUIRED_CONFIG: 不能被覆盖的设置项, 最高优先级 (e.g. /etc/clash/required.yaml)
      - CLASH_HTTP_PORT=7890   # optional (default:7890)
      - CLASH_SOCKS_PORT=7891  # optional (default:7891)
      - CLASH_TPROXY_PORT=7892 # optional (default:7892)
      - CLASH_MIXED_PORT=7893  # optional (default:7893)
      - DASH_PORT=8080         # optional (default:8080) RESTful API端口(对应WebUI http://IP:8080/ui)
      - DASH_PATH="/etc/clash/dashboard" # optional (default:"/etc/clash/dashboard/public")
      - IP_ROUTE=1             # optional (default:1) 开启透明代理(本机透明代理/作为旁路网关)
      - UDP_PROXY=1            # optional (default:1) 开启透明代理-UDP转发(需要节点支持)
      - IPV6_PROXY=1           # optional (default:1) 开启IPv6透明代理
      - LOG_LEVEL=info         # optional (default:info) 日志等级
      - ENABLE_SUBCONV=1       # optional (default:1) 开启本地订阅转换服务, 指定SUBSCR_URLS, 且没有外部订阅转换服务时, 需要为1
      - SUBCONV_URL=http://127.0.0.1:25500/sub  # optional (default:"http://127.0.0.1:25500/sub") 订阅转换服务地址
      - SUBSCR_URLS=<URLs split by '|'>         # optional 订阅的节点链接, 多个链接用'|'分隔, 会覆盖原有的config.yaml
      - SUBSCR_EXPR=86400                       # optional (default:86400) 订阅过期时间(秒), 下次启动如果过期, 会重新订阅
      # - REMOTE_CONV_RULE=<URL of remote rule>   # optional (default:⬇️) 订阅转换规则
      # REMOTE_CONV_RULE: 默认使用内部服务提供的链接 "http://127.0.0.1:8091/ACL4SSR/Clash/config/ACL4SSR_Online_Full.ini"
      # 在浏览器打开 http://< 服务器IP >:8091/ACL4SSR/Clash/config/ 即可查看内部服务支持的规则列表
      - EXPORT_DIR_PORT=8091
      - EXPORT_DIR_BIND=0.0.0.0
      - NO_ENGLISH=true        # optional (default:true) 提醒自己这玩意主要是国人用
    volumes:
      - <path to config>:/etc/clash # required config.yaml的存放路径
      - /dev:/dev                   # optional 用于自动挂载TPROXY模块
      - /lib/modules:/lib/modules   # optional 用于自动挂载TPROXY模块
    networks:
      chislash:
        ipv4_address: 192.168.1.12
    restart: unless-stopped
    
networks:
  chislash:
    external: true
    name: chislash
```
- docker run (参考docker-compose)

### 1. 开启网卡混杂模式
```shell
## 启用
ip link set eth0 promisc on
```
### 2. docker 创建 macvlan 网络
```shell
# subnet为你的网段
# gateway为你的网关
# chislash为你的macvlan 网络名
# 以下参数请根据你的实际情况修改
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  chislash
```
### 3. 启动 chislash 镜像
```shell
docker compose up -d
```



## 支持情况

| OS                            | 透明代理/网关(Transparent Gateway) | 服务端(HTTP/SOCKS5 Proxy Server) |
| ----------------------------- | ---------------------------------- | -------------------------------- |
| Linux (with tproxy module)    | ✅                                  | ✅                                |
| Linux (without tproxy module) | ❎                                  | ✅                                |
| Windows                       | ❓                                  | ❓                                |
| macOS                         | ❓                                  | ❓                                |

## 感谢
- https://github.com/Dreamacro/clash
- https://github.com/haishanh/yacd
- https://github.com/tindy2013/subconverter
- https://github.com/ACL4SSR/ACL4SSR
- https://github.com/gindex/chislash
