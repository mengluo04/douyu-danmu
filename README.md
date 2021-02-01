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
 3、将登录部分的username和userid的123456替换成你自己的uid，也可以随意一个，将74751替换成你自己的房间号  
 3、使用python3 danmu.py运行  
 
#####################2021年2月1日#####################

飞机火箭等大礼物消息类型type为 tsboxb   
对应的礼物id地段为rpt，用户昵称为snk  
礼物id可以从这个接口获取  
https://www.douyu.com/betard/74751  
74751为房间id，在room_gift字典的gift字典下面的effect字典里，treasure_type字段就是上面说到的rpt字段对应的值，name为礼物名称

全站礼物接口和小礼物接口  
https://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json （全站）
https://webconf.douyucdn.cn/resource/common/gift/gift_template/20003.json （小礼物）  
其中20003为当前直播间礼物模板id，通过https://www.douyu.com/betard/74751 中的 room.giftTempId 获取
