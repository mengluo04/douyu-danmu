import json
import time
import threading
from datetime import datetime
import pymysql
import requests
import websocket


class Spider(object):
    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', user='user', password='password', db='database', charset='utf8mb4')
        self.cursor = self.conn.cursor()
        self.ws = websocket.create_connection('wss://danmuproxy.douyu.com:8506')
        self.gift_dict = self.get_gift_dict()
        self.gift_dict_keys = self.gift_dict.keys()

    # 编码请求消息
    def dy_encode(self, msg):
        try:
            data_len = len(msg) + 9
            msg_byte = msg.encode('utf-8')
            len_byte = int.to_bytes(data_len, 4, 'little')
            send_byte = bytearray([0xb1, 0x02, 0x00, 0x00])
            end_byte = bytearray([0x00])
            data = len_byte + len_byte + send_byte + msg_byte + end_byte
            return data
        except:
            pass

    # 解码响应消息
    def dy_decode(self, msg_byte):
        try:
            pos = 0
            msg = []
            while pos < len(msg_byte):
                content_length = int.from_bytes(msg_byte[pos: pos + 4], byteorder='little')
                content = msg_byte[pos + 12: pos + 3 + content_length].decode(encoding='utf-8', errors='ignore')
                msg.append(content)
                pos += (4 + content_length)
            return msg
        except:
            pass

    # 解析响应消息
    def parse_msg(self, raw_msg):
        res = {}
        attrs = raw_msg.split('/')[0:-1]
        for attr in attrs:
            try:
                attr = attr.replace('@S', '/')
                attr = attr.replace('@A', '@')
                couple = attr.split('@=')
                res[couple[0]] = couple[1]
            except Exception as e:
                pass
        return res

    # 登录
    def login(self):
        """
        1.客户端向弹幕服务器发送登录请求
        2.客户端收到登录成功消息后发送进入弹幕分组请求给弹幕服务器
        """
        login_msg = "type@=loginreq/roomid@=74751/dfl@=/username@=123456=/uid@=123456/ver@=20190610/aver@=218101901/ct@=0/"
        try:
            self.ws.send(self.dy_encode(login_msg))
            print('登陆成功')
        except Exception as e:
            exit(1)

    # 加入分组，-9999为海量弹幕
    def join_group(self):
        join_group_msg = 'type@=joingroup/rid@=74751/gid@=-9999/'
        try:
            self.ws.send(self.dy_encode(join_group_msg))
            print('加入分组成功')
        except Exception as e:
            exit(1)

    # 获取消息
    def get_msg(self):
        print('开始接收消息')
        while True:
            try:
                msg_bytes = self.ws.recv()
                msg_arr = self.dy_decode(msg_bytes)
                msg = self.parse_msg(msg_arr[0])
                # 弹幕
                if msg['type'] == 'chatmsg':
                    self.parse_chatmsg(msg)
                # 禁言
                if msg['type'] == 'newblackres':
                    self.parse_newblackres(msg)
                #  礼物
                if msg['type'] == 'dgb':
                    self.parse_gift(msg)
            except Exception as e:
                exit(1)

    # 提取弹幕内容
    def parse_chatmsg(self, msg):
        item = {}
        try:
            content = msg['txt']
            content = content.replace('\\', '')
            content = content.replace('\'', '')
            content = content.replace('"', '')
            item['nickname'] = msg['nn']  # 昵称
            item['content'] = content  # 内容
            item['level'] = msg['level']  # 用户等级
            item['fan_card'] = msg['bnn']  # 粉丝牌
            item['send_time'] = datetime.now()
            item['fan_level'] = msg['bl']  # 粉丝牌等级
            self.add_dm_sql(item)
        except Exception as e:
            pass

    # 提取禁言信息
    def parse_newblackres(self, msg):
        item = {}
        try:
            item['snic'] = msg['snic']  # 禁言者昵称
            item['dnic'] = msg['dnic']  # 被禁言用户昵称
            item['otype'] = msg['otype']  # 禁言操作人类型
            item['endtime'] = msg['endtime']  # 禁言结束时间
            self.add_jy_sql(item)
        except Exception as e:
            pass

    # 提取礼物信息
    def parse_gift(self, msg):
        item = {}
        try:
            item['nickname'] = msg['nn']  # 用户昵称
            item['uid'] = msg['uid']  # 用户id
            item['gift_id'] = msg['gfid']  # 礼物id
            if msg['gfid'] in self.gift_dict_keys:
                item['gift_name'] = self.gift_dict[msg['gfid']]  # 礼物名称
            else:
                item['gift_name'] = '未知'
            item['level'] = msg['level']  # 用户等级
            item['gift_count'] = msg['gfcnt']  # 礼物个数
            item['fan_card'] = msg['bnn']  # 粉丝牌
            item['fan_level'] = msg['bl']  # 粉丝牌等级
            item['fan_card_room_id'] = msg['brid']  # 粉丝牌房间号
            item['receive_uid'] = msg['receive_uid']  # 主播uid
            item['receive_nn'] = msg['receive_nn']  # 主播昵称
            item['gift_from'] = msg['from']  # 礼物来源 2-背包
            item['send_time'] = datetime.now()
            self.add_gift_sql(item)
        except Exception as e:
            print(e)
            pass

    # 保存弹幕数据到数据库
    def add_dm_sql(self, obj):
        try:
            nickname = obj['nickname']
            content = obj['content']
            fan_card = obj['fan_card']
            fan_level = obj['fan_level']
            level = obj['level']
            send_time = obj['send_time']
            sql = "insert into douyu_danmu (nickname,content,user_level,fan_card,fan_level,send_time) values ('%s','%s','%s','%s','%s','%s')" % (
                nickname, content, level, fan_card, fan_level, send_time)
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.ping(reconnect=True)  # 检查连接是否断开，断开重连

    # 保存禁言数据到数据库
    def add_jy_sql(self, obj):
        try:
            snic = obj['snic']
            dnic = obj['dnic']
            otype = obj['otype']
            endtime = obj['endtime']
            timestamp = int(endtime)
            endtime = datetime.fromtimestamp(timestamp)
            sql = "insert into douyu_jinyan (snic,dnic,otype,endtime) values ('%s','%s','%s','%s')" % (
                snic, dnic, otype, endtime)
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.ping(reconnect=True)  # 检查连接是否断开，断开重连
        # 保存弹幕数据到数据库

    def add_gift_sql(self, obj):
        try:
            nickname = obj['nickname']
            uid = obj['uid']
            fan_card = obj['fan_card']
            fan_level = obj['fan_level']
            fan_card_room_id = obj['fan_card_room_id']
            user_level = obj['level']
            gift_id = obj['gift_id']
            gift_name = obj['gift_name']
            gift_count = obj['gift_count']
            receive_uid = obj['receive_uid']  # 主播uid
            receive_nn = obj['receive_nn']  # 主播昵称
            gift_from = obj['gift_from']
            send_time = obj['send_time']
            sql = "insert into douyu_gift (nickname,uid,user_level,fan_card,fan_level,fan_room_id,gift_id,gift_name,gift_count,gift_from,receive_uid,receive_nickname,send_time) " \
                  "values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
                  % (nickname, uid, user_level, fan_card, fan_level, fan_card_room_id, gift_id, gift_name, gift_count,
                     gift_from, receive_uid, receive_nn, send_time)
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(e)
            self.conn.ping(reconnect=True)  # 检查连接是否断开，断开重连

    # 心跳连接
    def keep_alive(self):
        print('建立初始心跳连接...')
        """
        客户端每隔 45 秒发送心跳信息给弹幕服务器
        """
        while True:
            try:
                msg = 'type@=mrkl/'
                self.ws.send(self.dy_encode(msg))
                time.sleep(45)
            except Exception as e:
                exit(1)

    # 礼物id映射
    def get_gift_dict(self):
        gift_json = {}
        gift_json1 = requests.get('https://webconf.douyucdn.cn/resource/common/gift/flash/gift_effect.json').text
        gift_json2 = requests.get(
            'https://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json').text
        gift_json3 = requests.get(
            'https://webconf.douyucdn.cn/resource/common/gift/gift_template/20003.json').text
        gift_json1 = gift_json1.lstrip('DYConfigCallback(').rstrip(');')
        gift_json2 = gift_json2.lstrip('DYConfigCallback(').rstrip(');')
        gift_json3 = gift_json3.lstrip('DYConfigCallback(').rstrip(');')
        gift_json1 = json.loads(gift_json1)['data']['flashConfig']
        gift_json2 = json.loads(gift_json2)['data']
        gift_json3 = json.loads(gift_json3)['data']
        for gift in gift_json1:
            gift_json[gift] = gift_json1[gift]['name']
        for gift in gift_json2:
            gift_json[gift] = gift_json2[gift]['name']
        for gift in gift_json3:
            gift_json[str(gift['id'])] = gift['name']
        print(gift_json)
        return gift_json


if __name__ == '__main__':
    print('启动程序...', time.strftime('%Y-%m-%d %H:%M:%S'))
    dm = Spider()
    dm.login()
    dm.join_group()
    t1 = threading.Thread(target=dm.get_msg)
    t2 = threading.Thread(target=dm.keep_alive)
    t2.setDaemon(True)
    t1.start()
    t2.start()
