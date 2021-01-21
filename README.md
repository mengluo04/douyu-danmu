# douyu-danmu
斗鱼弹幕获取和保存

已实现功能：
 1、普通消息弹幕的提取和保存
 2、房间禁言信息提取和保存
 3、普通礼物提取和保存
存在问题：
 1、可能有异常弹幕解析失败导致程序崩溃，可以使用supervisor进行监听
  2、飞机火箭等礼物在礼物类型dgb下无法获取

使用：
 1、安装requests，pymysql，websocket-client
 2、准备好数据库和表
 3、使用python3 danmu.py运行
