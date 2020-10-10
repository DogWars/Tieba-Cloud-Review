# -*- coding:utf-8 -*-
__all__ = ('CloudReview',)



import os
import sys
import time

import re
import json

from PIL import Image
from io import BytesIO
import pyzbar.pyzbar as pyzbar
import imagehash

import pypinyin as pinyin

import requests as req
import mysql.connector
from urllib.parse import unquote

from .__define__ import SHOTNAME
from ._mysql import _MySQL
from ._logger import log
from .admin_browser import AdminBrowser



class RegularExp(object):


    contact_exp = re.compile('(\+|加|联系|私|找).{0,2}我|(d|滴)我|(私|s)(信|我|聊)|滴滴|dd|didi',re.I)
    contact_rare_exp = re.compile('(在|看|→|👉|☞).{0,3}(我|俺).{0,3}((贴|帖)子|关注|主页|主业|资料|签名|尾巴|简介|(头|投)(像|象))|(头|投).(像|象)|主.页|(关注|主页|主业|资料|签名|尾巴|简介|(头|投)(像|象))(有|安排|上车)|威(信|辛)|(\+|加|联系|➕|十|＋|私|找|伽).{0,2}(威|薇|徾|徽|微|wx|v|q|企鹅|❤|蔻|寇)|(➕|十|＋|伽).{0,2}(我|俺)|(威|薇|威|微|wx|v|企鹅|❤|蔻|寇).{0,2}(:|：|号)|q.?\d{6,11}|有意.{0,3}(s|私)|连细方式|罔址|个.?性.?签.?名|簽|萜',re.I)

    course_exp = re.compile('摄影|视频(剪辑|特效)|后期|CAD|素描|彩铅|板绘|绘画|设计|ps|美术|国画|水彩|领取.{0,3}课程|英语口语|演唱|声乐|唱.{0,3}技巧|学历',re.I)
    course_check_exp = re.compile('交流群|课程|徒弟|素材|资料|教(程|学)|学习|邮箱|留言|扣.?1|想学|提升')

    app_nocheck_exp = re.compile('tao寳|tb口令|(淘宝|抖音).{0,2}(号|hao)|绿色.{0,2}平台|赛事预测|【支付宝】|解封微信|扫码.{0,3}送红包|关注.{0,2}微博|帮注册',re.I)
    app_exp = re.compile('拼(夕夕|多多|dd)|京(东|d)|抖音|支付宝|淘宝|火山小视频|微信|饿了么|美团|唯品会|苏宁|易购',re.I)
    app_check_exp = re.compile('点一下|点赞|任务|长按复制|复制整段话|账号|绿色|开店|店铺|运营|搜索|红包|福利|推广|聘|免费')

    business_exp = re.compile('【.{0,6}1[345789]\d{9}.{0,6}】|(高仿|复刻|购).{0,3}(鞋|包|表)|(潮|莆田).{0,2}鞋|工厂直供|品质保证|价格美丽|潮牌复刻|(实惠|羊毛).*群|撸货|线报|厂家货源|助力微商|迬页|#后期#.*做熟悉|绿色正规行业|价格可谈|金钱自由|零售商|网赌|火爆招商|电子商务|有限公司|公司注册|蓷廣|瀛到笑开花|教育品牌|引流招商|回馈客户|可接定制|培训辅导|(投放).{0,2}广|高(转化|收益)|借贷|朋友推荐.*产品|区块链',re.I)
    
    job_nocheck_exp = re.compile('想做单|宝妈[^妈]|(跟着|动手指).{0,2}赚钱|免费入职|(招|收).{0,4}(临时工|徒)|(在家|轻松).{0,2}(可|能|没事).?做|时间自由|煎直|兼耳只|勉费|上迁.*没问题|不收.?任何费用|包食宿|vx辅助|坚持.*日入过|赚米',re.I)
    job_exp = re.compile('佣金|押金|会费|培训|结算|(日|立)(结|洁)|高佣|想做的|有兴趣|稳赚|(一|每)(天|日|月)\d{2,3}|(日|月)(入|进).{0,2}(元|块|百|佰|万|w)|(利润|收益|工资|薪资|收入|福利|待遇)(高|好|\d{3,})|(高|好)(利润|收益|工资|薪资|收入|福利|待遇)|低(风险|投入)|风险低|合作愉快|手机.*就(行|可)|(有|一).?手机|包学会|包分配|工作(轻松|简单)|不收(米|钱)',re.I)
    job_check_exp = re.compile('暑假工|临时工|短期工|兼职|主播|声播|签约艺人|模特|陪玩|写手|(点赞|接单)员|工作室|手工|项目|电商|创业|自媒体|加盟|副业|代理|(免费|需要|诚信|诚心)(带|做)|想(赚|挣)钱|不甘.?现状.*兄弟|有想.*的(朋友|兄弟)|(刷|做)(单|销量)|微商|投资|写好评|不嫌少|需工作|号商|形象好|气质佳|转发朋友圈|手工活')
    
    game_exp = re.compile('手游.{0,7}(神豪|托|演员|充值)|招.{0,4}(托|内部|人员|内玩)|找.{0,4}内玩|要找试玩|新区开服|霸服|你想要玩的手游|(游戏|内部|手游)体验员|(玩家|手游|游戏|每天都有|充值)福利|喜欢玩.*仙侠|(日|天|送|领|给你|免费).{0,2}648|手蝣|私服|(手游|游戏)推广|手游.{0,2}招|(游戏|内部|手游).*(资源|福利)号|(仙侠|国战).{0,2}(游戏|手游)|游戏.{0,2}单|(当|做)游戏主播|开了个手游|来就.{0,2}送|遊|戲|號|ux63',re.I)

    name_nocheck_exp = re.compile('魸|莆田|^.{2}🔥$|^轰炸(软件|机)|老司机看片|导航|引流')
    name_exp = re.compile('😍|☜|☞')
    name_check_exp = re.compile('资(源|料)|wx|\d{5,}|企鹅|(头|投)(像|象)|(主|煮)页|签名')

    maipian_exp = re.compile('(下|↓).{0,3}有惊喜|成人看的|小情侣|桌子上都是水|注意身体|推荐.{0,3}资源|回复.*:你(帖|贴).*可以看|自己上微.?薄|自己.*捜|都有.*看我关注的人|experience\+.{0,8}#.*#|看偏神器|学姐给我吃|推荐发展对象|脱单|^麦片$|卖淫|嫂子直接.*那个|小哥哥们.*看我|进去.*弄得喷水|(看|有)女神|噜.?个月|鲁管',re.I)
    female_check_exp = re.compile('9\d年|有人聊|聊天|女汉纸|女神|表姐|宅女|老娘|阿姨|好孤单|男盆友|渣男|男生|朋友|睡不着|恋爱|爱会消失|交友|爱情|对象|处.?友|奔现|网恋|约会|(超|甜)甜|干点啥|对我做|无聊|手牵手|我的b|被你骑|(約|悦)炮|哥哥|小(姐姐|妹妹|gg)|好想你|勾搭|(大|小)可爱|憋疯了|认识一下|我.?有趣|呆在家里|带个人回家|相个?亲|认真处|真心|性感|希望遇到|嫁不出去|本人女|撩|列表|大叔|越来越懒|好友|可悦|签收|手纸')

    hospital_exp = re.compile('医院.*好不好|狐臭|痔疮|性腺|阳痿|早泄|不孕不育|前列腺|妇科|会所')

    lv1_exp = re.compile('公众号|传媒|新媒体|婚恋|财经|鱼胶|信︄用卡|看手相|出租|塔罗|代骂服务|问卷调查|呺|核雕|莆田|【.*?】.*(#.*?#|【.*?】)|闲时无聊|有意者|(邪|手)淫.{0,3}危害|急需.{0,10}钱')

    kill_thread_exp = re.compile('@(小度🎁活动🔥|小度º活动君|活动🔥小度🎁)|特价版App|淘宝特价版',re.I)



class MySQL(_MySQL):
    """
    为云审查重载的MySQL链接类
    """


    __slots__ = ('tb_name_eng',)


    def __init__(self,db_name,tb_name_eng):
        super(MySQL,self).__init__(db_name)
        self.tb_name_eng = tb_name_eng

        self.mycursor.execute("SHOW TABLES LIKE 'pid_whitelist_{}'".format(tb_name_eng))
        if not self.mycursor.fetchone():
            self.mycursor.execute("CREATE TABLE pid_whitelist_{} (pid BIGINT NOT NULL PRIMARY KEY, record_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)".format(tb_name_eng))
            self.mycursor.execute("""CREATE EVENT event_auto_del_pid_whitelist_{tb_name}
            ON SCHEDULE
            EVERY 1 DAY STARTS '2000-01-01 00:00:00'
            DO
            DELETE FROM pid_whitelist_{} WHERE record_time<(CURRENT_TIMESTAMP() + INTERVAL -15 DAY)""".format(tb_name_eng))


    def add_pid(self,pid):
        """
        插入pid
        add_pid(pid)
        """

        try:
            self.mycursor.execute("INSERT IGNORE INTO pid_whitelist_{tb_name} VALUES (%s,DEFAULT)".format(tb_name=self.tb_name_eng),(pid,))
        except mysql.connector.errors.DatabaseError:
            log.error("MySQL Error: Failed to insert {pid}!".format(pid=pid))
            return False
        else:
            self.mydb.commit()
            return True


    def has_pid(self,pid):
        """
        检索是否已有pid
        has_pid(pid)
        """

        try:
            self.mycursor.execute("SELECT NULL FROM pid_whitelist_{tb_name} WHERE pid={pid}".format(tb_name=self.tb_name_eng,pid=pid))
        except mysql.connector.errors.DatabaseError:
            log.error("MySQL Error: Failed to select {pid}!".format(pid=pid))
            return False
        else:
            return True if self.mycursor.fetchone() else False


    def del_pid(self,hour):
        """
        删除最近hour个小时记录的pid
        del_pid(hour)
        """
        try:
            self.mycursor.execute("DELETE FROM pid_whitelist_{tb_name} WHERE record_time>(CURRENT_TIMESTAMP() + INTERVAL -{hour} HOUR)".format(tb_name=self.tb_name_eng,hour=hour))
        except mysql.connector.errors.DatabaseError:
            log.error("MySQL Error: Failed to delete pid in pid_whitelist_{tb_name}".format(tb_name=self.tb_name_eng))
            return False
        else:
            self.mydb.commit()
            log.info("Successfully deleted pid in pid_whitelist_{tb_name} within {hour} hour(s)".format(tb_name=self.tb_name_eng,hour=hour))
            return True


    def iswhite_portrait(self,portrait):
        """
        检索portrait的黑白名单状态
        iswhite_portrait(portrait)

        返回值:
            iswhite: True 白名单 / False 黑名单 / None 不在名单中
        """

        try:
            self.mycursor.execute("SELECT is_white FROM portrait_{tb_name} WHERE portrait='{portrait}' LIMIT 1".format(tb_name=self.tb_name_eng,portrait=portrait))
        except mysql.connector.errors.DatabaseError:
            return None
        else:
            res_tuple = self.mycursor.fetchone()
            if res_tuple:
                return True if res_tuple[0] else False
            else:
                return None



class CloudReview(AdminBrowser):
    """
    云审查基类
    CloudReview(BDUSS_key,tb_name,tb_name_eng,cycle_times=1,sleep_time=0)

    参数:
        BDUSS_key: str 作为键值从user_control/BDUSS.json中取出BDUSS
        tb_name: str 贴吧名
        tb_name_eng: str 贴吧英文名，仅用于连接数据库
        cycle_times: int 每次脚本启动后进行的云审查次数
        sleep_time: float 每两次云审查的间隔时间
    """


    __slots__ = ('tb_name','tb_name_eng',
                 'sleep_time','cycle_times',
                 'exp',
                 'mysql')


    def __init__(self,BDUSS_key,tb_name,tb_name_eng,cycle_times=1,sleep_time=0):
        super(CloudReview,self).__init__(BDUSS_key)

        self.tb_name = tb_name
        self.tb_name_eng = tb_name_eng
        self.sleep_time = sleep_time
        self.cycle_times = cycle_times

        self.mysql = MySQL('tieba_pid_whitelist',tb_name_eng)

        self.exp = RegularExp()


    def quit(self):
        self.mysql.quit()
        super(CloudReview,self).quit()


    def add_portrait(self,portrait=None,user_name=None,mode=True):
        """
        向名单中插入portrait
        add_portrait(portrait=None,user_name=None,mode=True)
        """

        if type(mode) != bool:
            log.error("Wrong mode in _mysql_add_portrait!")
            return False

        if not (portrait or user_name):
            log.error("Both portrait and user_name are None!")
            return False

        if portrait:
            user_name = self._portrait2names(portrait)[0]
        else:
            portrait = self._name2portrait(user_name)

        try:
            self.mysql.mycursor.execute("INSERT INTO portrait_{tb_name} VALUES (%s,%s,%s,DEFAULT) ON DUPLICATE KEY UPDATE is_white={mode}".format(tb_name=self.tb_name_eng,mode=mode),(portrait,user_name,mode))
        except mysql.connector.errors.DatabaseError:
            log.error("MySQL Error: Failed to insert {portrait}!".format(portrait=portrait))
            return False
        else:
            log.info("Successfully added {portrait}/{user_name} to table of {tb_name} mode:{mode}".format(portrait=portrait,user_name=user_name,tb_name=self.tb_name_eng,mode=mode))
            self.mysql.mydb.commit()
            return True


    def del_portrait(self,portrait=None,user_name=None):
        """
        从名单中删除portrait
        del_portrait(portrait=None,user_name=None)
        """

        if not (portrait or user_name):
            log.error("Both portrait and user_name are None!")
            return False

        if portrait:
            user_name = self._portrait2names(portrait)[0]
        else:
            portrait = self._name2portrait(user_name)

        try:
            self.mysql.mycursor.execute("DELETE FROM portrait_{tb_name} WHERE portrait='{portrait}'".format(tb_name=self.tb_name_eng,portrait=portrait))
        except mysql.connector.errors.DatabaseError:
            log.error("MySQL Error: Failed to delete {portrait}!".format(portrait=portrait))
            return False
        else:
            log.info("Successfully deleted {portrait}/{user_name} from table of {tb_name}".format(portrait=portrait,user_name=user_name,tb_name=self.tb_name_eng))
            self.mysql.mydb.commit()
            return True


    def _url2image(self,img_url:str):
        """
        从链接获取静态图像
        """

        if not re.search('\.(jpg|jpeg|png)',img_url):
            log.error('Failed to get {url}'.format(url=img_url))
            return None

        self._set_host(img_url)
        retry_times = 5
        image = None
        while retry_times:
            try:
                res = req.get(img_url,headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    try:
                        image = Image.open(BytesIO(res.content))
                    except OSError:
                        return None
                    break
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