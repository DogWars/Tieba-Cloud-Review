# -*- coding:utf-8 -*-
__all__ = ('CloudReview',)



import os
import sys
import time
import platform
from io import BytesIO

import re
import json

import requests as req
import mysql.connector
from urllib.parse import unquote

from PIL import Image
import pyzbar.pyzbar as pyzbar
import imagehash

import pypinyin as pinyin

from .admin_browser import AdminBrowser,log
from ._logger import SHOTNAME



DB_NAME = 'tieba_pid_whitelist'  # 数据库名
system = platform.system()
if system == 'Linux':
    mysql_login = {
        'host':'starry-qvq.mysql.rds.aliyuncs.com',
        'user':'starry',
        'passwd':'40Ar40K-'
        }  # 链接所需的用户名和密码
else:
    mysql_login = {
        'host':'starry-ovo.mysql.rds.aliyuncs.com',
        'port':4396,
        'user':'starry',
        'passwd':'40Ar40K-'
        }



class CloudReview(AdminBrowser):
    """
    CloudReview(headers_filepath,ctrl_filepath)

    云审查基类
        参数: raw_headers 字典 包含cookies的原始头
              ctrl_filepath 字符串 控制云审查行为的json的路径
    """


    __slots__ = ('tb_name','tb_name_eng',
                 'ctrl_filepath','sleep_time','cycle_times',
                 'exp',
                 'mydb','mycursor')


    def __init__(self,headers_filepath,ctrl_filepath):
        self.ctrl_filepath = ctrl_filepath
        review_control = self._link_ctrl_json(ctrl_filepath)
        super(CloudReview,self).__init__(headers_filepath,review_control['admin_type'])

        try:
            self.tb_name = review_control['tieba_name']
            self.tb_name_eng = review_control['tieba_name_eng']
            self.sleep_time = review_control['sleep_time']
            self.cycle_times = review_control['cycle_times']
        except AttributeError:
            log.critical('Incorrect format of ctrl json!')
            raise(AttributeError('Incorrect format of ctrl json!'))

        try:
            self.mydb = mysql.connector.connect(database=DB_NAME,**mysql_login)
        except (mysql.connector.errors.ProgrammingError):
            self.mydb = mysql.connector.connect(**mysql_login)
            self.mycursor = self.mydb.cursor()
            self.mycursor.execute("CREATE DATABASE {database}".format(database=DB_NAME))
            self.mycursor.execute("USE {database}".format(database=DB_NAME))
        except (mysql.connector.errors.DatabaseError):
            log.critical('Cannot link to the database!')
            raise(mysql.connector.errors.DatabaseError('Cannot link to the database!'))
        else:
            self.mycursor = self.mydb.cursor()

        self.mycursor.execute("SHOW TABLES LIKE 'pid_whitelist_{tb_name}'".format(tb_name=self.tb_name_eng))
        if not self.mycursor.fetchone():
            self.mycursor.execute("CREATE TABLE pid_whitelist_{tb_name} (pid BIGINT NOT NULL PRIMARY KEY, portrait CHAR(36) NOT NULL, record_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)".format(tb_name=self.tb_name_eng))
            self.mycursor.execute("""CREATE EVENT event_auto_del_pid_whitelist_{tb_name}
            ON SCHEDULE
            EVERY 1 DAY STARTS '2000-01-01 00:00:00'
            DO
            DELETE FROM pid_whitelist_{tb_name} WHERE record_time<(CURRENT_TIMESTAMP() + INTERVAL -15 DAY)""".format(tb_name=self.tb_name_eng))

        self.exp = RegularExp()


    def quit(self):
        self.mydb.commit()
        self.mydb.close()
        super(CloudReview,self).quit()


    def _mysql_add_pid(self,pid,portrait):
        """
        向MySQL中插入pid
        """

        try:
            self.mycursor.execute("INSERT IGNORE INTO pid_whitelist_{tb_name} VALUES (%s,%s,DEFAULT)".format(tb_name=self.tb_name_eng),(pid,portrait))
        except (mysql.connector.errors.DatabaseError):
            log.error("MySQL Error: Failed to insert {pid}!".format(pid=pid))
        else:
            self.mydb.commit()


    def _mysql_search_pid(self,pid):
        """
        检索MySQL中是否已有pid
        """

        try:
            self.mycursor.execute("SELECT NULL FROM pid_whitelist_{tb_name} WHERE pid={pid} LIMIT 1".format(tb_name=self.tb_name_eng,pid=pid))
        except (mysql.connector.errors.DatabaseError):
            log.error("MySQL Error: Failed to select {pid}!".format(pid=pid))
            return False
        else:
            return True if self.mycursor.fetchone() else False


    def _mysql_search_portrait(self,portrait):
        """
        检索portrait是否位于黑白名单中，若是则返回is_white值
        """

        try:
            self.mycursor.execute("SELECT is_white FROM portrait_{tb_name} WHERE portrait='{portrait}' LIMIT 1".format(tb_name=self.tb_name_eng,portrait=portrait))
        except (mysql.connector.errors.DatabaseError) as e:
            return None
        else:
            res_tuple = self.mycursor.fetchone()
            if res_tuple:
                return True if res_tuple[0] else False
            else:
                return None


    def _mysql_add_portrait(self,portrait = None,user_name = None,mode = True):
        """
        向名单中插入portrait
        """
        if type(mode) != bool:
            log.error("Wrong mode in _mysql_add_portrait!")
            return

        if not portrait and user_name:
            portrait = self._name2portrait(user_name)
        elif not user_name and portrait:
            user_name = self._portrait2names(portrait)[0]
        else:
            log.error("Both portrait and user_name are None!")

        try:
            self.mycursor.execute("INSERT INTO portrait_{tb_name} VALUES (%s,%s,%s,DEFAULT) ON DUPLICATE KEY UPDATE is_white={mode}".format(tb_name=self.tb_name_eng,mode=mode),(portrait,user_name,mode))
        except (mysql.connector.errors.DatabaseError):
            log.error("MySQL Error: Failed to insert {portrait}!".format(portrait=portrait))
        else:
            self.mydb.commit()


    def _url2image(self,img_url:str):
        """
        从链接获取静态图像
        """

        if re.search('\.(bmp|gif)',img_url):
            log.error('Failed to get {url}'.format(url=img_url))
            return None

        self._set_host(img_url)
        retry_times = 5
        image = None
        while retry_times:
            try:
                res = req.get(img_url,headers=self.account.headers)
            except req.exceptions.RequestException:
                retry_times-=1
                time.sleep(0.5)
            else:
                if res.status_code == 200:
                    try:
                        image = Image.open(BytesIO(res.content))
                    except OSError:
                        return None
                    break
                else:
                    retry_times-=1
                    time.sleep(0.5)

        if not image:
            log.error('Failed to get image {url}'.format(url=img_url))
            return None

        return image


    def _scan_QRcode(self,img_url:str):
        """
        扫描img_url指定的图像中的二维码
        """

        image = self._url2image(img_url)
        if not image:
            return None

        raw = pyzbar.decode(image)
        if raw:
            data = unquote(raw[0].data.decode('utf-8'))
            return data
        else:
            return None


    def _get_imgdhash(self,img_url):
        """
        获取链接图像的dhash值
        """

        image = self._url2image(img_url)
        if not image:
            return None

        dhash = imagehash.dhash(image)
        return dhash


    def _homophones_check(self,check_str:str,words:list):
        """
        检查非常用谐音
        """

        def __get_pinyin(_str):
            pinyin_list = pinyin.lazy_pinyin(_str,errors='ignore')
            pinyin_str = ' '.join(pinyin_list)
            return pinyin_str

        check_pinyin = __get_pinyin(check_str)
        for word in words:
            if word not in check_str and __get_pinyin(word) in check_pinyin:
                return True

        return False


    @staticmethod
    def _link_ctrl_json(ctrl_filepath):
        """
        链接到一个控制用的json
        """
        
        try:
            with open(ctrl_filepath,'r',encoding='utf-8-sig') as review_ctrl_file:
                review_control = json.loads(review_ctrl_file.read())
        except (FileExistsError):
            raise(FileExistsError('review control json not exist! Please create it!'))
        else:
            return review_control



class RegularExp(object):


    contact_exp = re.compile('(\+|加|联系|私|找).{0,2}我|(d|滴)我|(私|s)(信|我|聊)|滴滴|dd|didi',re.I)
    contact_rare_exp = re.compile('(在|看|→|👉|☞).{0,3}我.{0,3}(关注|主页|资料|签名|尾巴|简介|(头|投)(像|象))|(关注|主页|资料|签名|尾巴|简介|(头|投)(像|象))有|威信|(\+|加|联系|➕|＋|私|找|伽).{0,2}(薇|徾|徽|微|wx|v|q|企鹅|❤)|(➕|＋|伽).{0,2}我|(薇|威|微|wx|v|企鹅|❤).{0,2}(:|：|号)|q.?\d{6,11}|有意.{0,3}(s|私)|连细方式|罔址')

    course_exp = re.compile('摄影|视频(剪辑|特效)|后期|CAD|素描|彩铅|板绘|绘画|设计|ps|美术|国画|水彩|领取.{0,3}课程|英语口语|演唱|声乐',re.I)
    course_check_exp = re.compile('交流群|课程|徒弟|素材|资料|教(程|学)|学习|邮箱|留言|扣.?1|想学',re.I)

    app_nocheck_exp = re.compile('淘tao寳|tb口令|(淘宝|抖音).{0,2}(号|hao)|绿色.{0,2}平台|赛事预测')
    app_exp = re.compile('拼(夕夕|多多|dd)|京(东|d)|抖音|支付宝|淘宝|火山小视频')
    app_check_exp = re.compile('点一下|点赞|任务|长按复制|复制整段话|账号|绿色|开店|店铺|运营|搜索')

    business_exp = re.compile('【.{0,6}1[345789]\d{9}.{0,6}】|(高仿|复刻).{0,2}表|潮鞋|潮牌复刻|(实惠|羊毛).*群|撸货|线报|厂家货源|助力微商|迬页|#后期#.*做熟悉|绿色正规行业|价格可谈|金钱自由|零售商|网赌|火爆招商|电子商务|有限公司|公司注册',re.I)
    
    job_nocheck_exp = re.compile('想做单|宝妈[^妈]|跟着.{0,2}赚钱|免费入职|(招|收).{0,4}(临时工|徒)|(在家|轻松)(可|就能|没事)做|时间自由|煎直|兼耳只|勉费|上迁.*没问题')
    job_exp = re.compile('暑假工|临时工|短期工|兼职|主播|声播|模特|陪玩|写手|点赞员|工作室|手工|项目|电商|创业|自媒体|加盟|副业|代理|(免费|需要|诚信|诚心)(带|做)|想(赚|挣)钱|不甘.?现状.*兄弟|有想.*的(朋友|兄弟)|(刷|做)(单|销量)|微商|投资|写好评|不嫌少|需工作|号商|形象好|气质佳',re.I)
    job_check_exp = re.compile('招|聘|佣金|押金|会费|培训|日(结|洁)|高佣|想做的|有兴趣|稳赚|(一|每)(天|日|月)\d{2,3}|(日|月)(入|进).{0,2}(元|块|百|佰|万|w)|(利润|收益|工资|薪资|收入)(高|\d{3,})|高(利润|收益|工资|薪资|收入)|低(风险|投入)|风险低|合作愉快|手机.*就(行|可)|有.?手机||包学会|包分配|工作(轻松|简单)',re.I)
    
    game_exp = re.compile('手游.{0,7}(神豪|托|演员|充值)|招.{0,4}(托|内部|人员|内玩)|新区开服|霸服|你想要玩的手游|(游戏|内部|手游)体验员|(玩家|手游|每天都有|充值)福利|喜欢玩.*仙侠|(每日|送|领).{0,2}648|手蝣|私服|(手游|游戏)推广|手游.{0,2}招|(游戏|内部|手游).*(资源|福利)号|仙侠游戏|游戏.{0,2}单|(当|做)游戏主播|开了个手游|手游.com',re.I)

    name_nocheck_exp = re.compile('魸|莆田')
    name_exp = re.compile('😍|☜|☞')
    name_check_exp = re.compile('资(源|料)|wx|\d{5,}|企鹅|(头|投)(像|象)|(主|煮)页|签名|^🌞菲儿.{2}\w')

    maipian_exp = re.compile('(下|↓).{0,3}有惊喜|成人看的|小情侣|桌子上都是水|注意身体|推荐.{0,3}资源|回复.*:你(帖|贴).*可以看|自己上微.?薄|自己.*捜|都有.*看我关注的人|experience\+.{0,8}#.*#|看偏神器|学姐给我吃|推荐发展对象|脱单|^麦片$|卖淫|嫂子直接.*那个|小哥哥们.*看我|进去.*弄得喷水',re.I)
    female_check_exp = re.compile('聊天|女神|表姐|好孤单|男盆友|渣男|朋友|睡不着|恋爱|宅女一枚|交友|老阿姨|爱情|对象|奔现|我超甜|好无聊啊|手牵手|和我的b一样|可以被你骑|(約|悦)炮|哥哥|好想你|求勾搭',re.I)

    hospital_exp = re.compile('医院.*好不好|狐臭|痔疮|性腺|阳痿|早泄|不孕不育|前列腺|妇科|会所')

    lv1_exp = re.compile('公众号|传媒|新媒体|婚恋|财经|鱼胶|信︄用卡|看手相|出租|塔罗|代骂服务|问卷调查')


    def __init__(self):
        pass