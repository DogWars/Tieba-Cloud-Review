# Tieba-Cloud-Review
部署于Linux系统的百度贴吧云审查&循环封禁Python脚本
## 功能特点
### 优点
+ 此脚本以客户端版API为主，以网页版API做备用，分别开发一套接口函数
+ 客户端版阅览API支持获取楼中楼等级、小尾巴、帖子（包括主题帖、回复、楼中楼）赞踩、用户性别，较网页版内容更多，速度更快
+ 不同于其他任何已有的贴吧开源脚本（仅支持通过用户名越权封禁），此脚本逆向完成的客户端版封禁API支持小吧主/语音小编对无用户名用户封禁十天
+ 集成大量大吧主权限相关的API，包括2020年最新的“大吧主首页推荐”功能
+ 得益于Python语言的强大扩展能力，脚本可以支持二维码识别、拼音谐音辨识、基于图像hash的相似度检测、jieba分词等扩展功能
+ 自定义修改函数，不再拘束于“傻瓜式”脚本的关键词组合判断，而是可以定义复杂的正则表达式，从用户等级/评论图片等等方面入手判断删帖与封禁条件
+ 使用MySQL辅助记录，大幅加速违规判断过程

### 缺点
- 需要一定的Python&Linux编程基础
- 现有功能需要MySQL支持
- 需要大量依赖项，脚本部署困难

## 环境部署

第一步环境部署对初学者而言极其困难，如果第一步你就做不下去建议放弃使用该脚本

+ 下载压缩包并在任一目录里解包，目录示例: **/root/scripts/tieba**

+ 配置MySQL

    + 使用该脚本，你需要一个MySQL数据库用来存储黑白名单用户以及pid白名单，以节约判断过程的耗时
    
    + 打开: **/browser/cloud_review.py**
    
        - 修改开头的**DB_NAME**可指定数据库名
        - 修改字典**mysql_login**来连接到你的MySQL数据库
        
+ pip安装需要的Python库
```
sudo pip3 install mysql-connector
sudo pip3 install lxml
sudo pip3 install bs4
sudo pip3 install pillow
sudo yum install zbar-devel
sudo pip3 install pyzbar
```
+ 附加说明

    + 如果**zbar-devel**安装失败
    
        + 你可能需要安装一个第三方yum源
        + Raven源 <https://centos.pkgs.org/8/raven-x86_64/raven-release-1.0-1.el8.noarch.rpm.html>
        + 使用```rpm -Uvh xxx.rpm```来安装Raven源
        
    + 各第三方库的用途说明
    
        + **mysql-connector** 连接MySQL
        + **lxml** 用于BeautifulSoup解析
        + **bs4** BeautifulSoup解析HTML
        + **pillow** 图像库
        + **zbar-devel** 二维码检测的底层支持代码
        + **pyzbar** 它是zbar的一个Python封装
        
## 自定义设置
脚本接受**命令行参数**，并通过**user_control文件夹里的json**来控制其行为

**命令行参数**都有默认值，所以一般不需要你特意设置

例如**example.py**对应的控制json就是**example.json**

下面说明这些json里各项值的意义

+ block_cycle.json
    
    + **block_list** 需要封禁的用户列表
    
        + **tb_name** 封禁将发生在哪个吧
        + **user_name** 被封禁人的用户名
        + **nick_name** 被封禁人的昵称（可选参数）
        + **day** 封禁天数
        + **portrait** 被封禁人的头像portrait值（可选参数）
        + **reason** 封禁理由（可选参数）
        
+ cloud_review.json

    + **tieba_name** 开启云审查的贴吧名
    + **sleep_time** 每两次循环审查的间隔时间
    + **cycle_times** 循环审查次数
    + **quit_flag** 是否在本次审查结束后退出，你可以随时修改该项来实现脚本的安全结束（退出时脚本会更新fid缓存、将仍未提交的语句提交到数据库）
    
+ headers.txt

    + 保存有cookies信息的头文件
    + 建议随便点开一个吧，按<kbd>F12</kbd>，在**Network**里将消息头直接复制到该txt中
    
## 自定义审查行为
请参照我给出的例子自己编程修改**cloud_review.py**，注释比较规范全面，请自行理解各api的功能

## 设置定时任务
给出我的crontab设置作为示例
```
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=""
25 0 * * * . /etc/profile; python /(屏蔽)/block_cycle.py -bc /(屏蔽)/block_cycle_1.json
0 0 */3 * * . /etc/profile; python /(屏蔽)/block_cycle.py -bc /(屏蔽)/user_control/block_cycle_10.json
*/6 6-23,0 * * * . /etc/profile; python /(屏蔽)/cloud_review.py
*/20 1-5 * * * . /etc/profile; python /(屏蔽)/cloud_review.py
```

## 结束
至此，所有的配置工作已经完成

**Enjoy :)**
