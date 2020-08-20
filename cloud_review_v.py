#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
2020-08-17 22:32更新
1、借助词频统计丰富v吧常用词汇表
2、分拆出course_exp（课程类广告）和job_exp（兼职类广告），并设置对应的xxx_check_exp（二次检查）
"""
import os
import sys
import time
import argparse

import re
import browser

import imagehash



PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')



class CloudReview(browser.CloudReview):


    __slots__ = ('vz_white_list',
                 'white_kw_exp',
                 'black_imghash',
                 'nullhead_imghash')


    def __init__(self,headers_filepath,ctrl_filepath):
        super(CloudReview,self).__init__(headers_filepath,ctrl_filepath)

        white_kw_list = ['vup|vtb|vtuber|管人|(几个|哪个|什么|的)v',
                         '(a|b|睿|皇协|批|p)站|海鲜|v吧|v8|nga|404|油管|ytb|油土鳖|论坛|字幕组|粉丝群',
                         '4v|樱花妹|中之人|国v|个人势|holo|虹|🌈|2434|杏|vr|木口|猴楼|大家庭',
                         '😅|👿|🐜|🤡|🏃|🐮|😨|👅',
                         '配信|联动|歌回|台词回|杂谈|歌力|企划|隐退|毕业|转生|复活|前世|sc|弹幕|二次元|开播|取关',
                         '如何评价|不懂就问|大的来了|很喜欢|我命令|速来|啊这|麻了|az|sj|懂.都懂|懂完了|4d|dddd|yyds|cylx|冲冲冲|反串|缝合|太嗯|不用.?多说了吧|细说|谜语|拉胯|虚无|牛大了|真不熟|成分|黑屁|破防|真可怜|发病|开团|(好|烂)活|干碎|对线|整活|批爆|乐了|乐子|橄榄|罢了|确实|可爱|芜湖|钓鱼|梁木|节奏|冲锋|yygq|芜狐|不如意|直播间|别尬|离谱|天使|母人|阴间|这波|泪目',
                         '懂哥|孝子|蛆|(大|带)(伙|🔥)|xdm|老哥|懂哥|mmr|萌萌人|gachi|anti|粉丝|太监|天狗|利普贝当|crew|杏奴|贵物|沙口|小鬼|后浪','爬|爪巴|滚|gck|有病吧']
        self.white_kw_exp = re.compile('|'.join(white_kw_list),re.I)

        self.vz_white_list = ['Mafia文','议会记录者','量子化的猪','小小boge','和儿qwq','民族团结徧','qq751122423','童子军追猎者','不色的外村','馃惗馃憡miss',
                             '可耐的小黑','寄你太霉','旋旋丶琳','wuhdhgd','一之濑丶姬月','骑20猪打100狗','那些年_很天真','juzhong71051','gyxer','勤奋的一醉方休',
                             '言之凿凿o','北岛字修','利啄恐惧','毒蛇王维诺米隆','未知错误已发生','推倒我的茶姬','霖下雨沫','中东将军','花花公孑','HikariBs丶',
                             '888888gua','殷子珺Esther','大漠的孤骑','不给力_有木有','安柒ゝ莫莫莫','asstiker','黑基佬2001','我们就不横山美','脸朝上上天堂',
                             '小张raning','plmnji1987','superslience','爱1再挥霍nice','Andacoco','EIDOS4','EDhundz','沧蓝色的旋律','夜雪灬微凉','a764928092',
                             '初心永一','林林DZL','四月土地i','护蛋小英雄','星际要塞','Perisuki','laorentouyu','初音_Mi_ku','erjunmeng','娘版死之翼','ASDDA563',
                             'Fearuine','垣根算个球啊','丢你雷姆和拉姆','不露姓名的沙雕','风之翼神','servant灬小莫','classover君','a1378535','qianjiale88',
                             '我爱脸盘','Yuntry','家族ad','廀簪','罗伯特々霍利','aq2910504','丿焰丶233','_Yakumo_','草你妹你妹啊55','确实懂得都懂','狂叫的猫',
                             '残阳已坠','神论螺丝钉','报废的幻想','香喷喷的rbq','你的基友是李刚','大大法法year','dsaasdhappy','窀穸殪殒','勤奋的发的22',
                             '怎么不会了么','奥特之神诺亚','爱慕梅神','伊吹萃瓜','永远的圆桌骑士','苍穹無爱','咯咯咯263','你我都是nt嗷','AIDWD时代','大羽纪事',
                             'uneeew','磾v反应','擦桌子擦地','十年单推人','你猜我叫shen','久佣深情','fate一stay','一个帅气的道士','天蝎GXKB','青山舍长',
                             '星空2月世界','手动档的火箭','AyaTsui','贫乏神来了4444','不必拥有名字','月丿美兔','某丝巾萨马','ice_orb','vtb鑸旔煇','无星夜D',
                             'ysbww','雷缪永恒','猩红溜溜男爵','槿染染','勺子习','歌弥山_c某某某','论外不是基佬','人民公仆42','2020年5月21','tnustc123','ctdls',
                             '无敌大手猪','绝体绝命IXA','阿腐腐腐腐腐','爱啊时','黎兆伦','天辰荒莽','TIGAEX','我愿忘记痛苦','hallo芝麻','呆秋','greenslime0',
                             'cx991230','黑井柴shiba','zakuzaku00','雷炎狂鹰','摇曳我的小青春','dy2084','HemisDivine','影神子','zl70971','批评家之死','十香大好',
                             '堕天使佳佳萌','人生意义在于SM','小明小伙','LIREICHENG','蓝天下的孩子们','651541897','染雪喵喵','18948599360','kallensama','gv890',
                             '炎炎炎炎焱','AAASLAN','matsuri7216','水边鳄','dyz1148301300','亚波人三世','咖啡x布丁','灬凡人的智慧','科学ikaros','百鬼_绫目',
                             '起名是真滴难受','zfyjfshit','xyh1102028057','Marion_Chen','真不是打广告','宅里乾坤大','sfmty123','诚如楼主之所言','哝煍杯北',
                             '智者不是智障','乡音___','消逝尽头的希望','大八神暗','水瓶lyc1111','Senpaiiii','微谷行','pekogachi','达酚蹄打喷嚏','太太尉',
                             '风卷残云FF','一童言无忌一1','与卿同偕老','王梅61','wannaknow_RAII','swhat','zhangxiaohuasm','汤圆tanen','23333兰颖','clzgdh',
                             '一只小葵熊55','雪雨明夜','掰兜','欼棗騕掔','FCQ123456abc','挽尊的朋友交易','SHDJAHDJASHDJ','幽冥毒皇丶飞跃','丿魔王丶','寄吧老大了',
                             'lucile_','大洋哥的小妹','射手445qw','小鱿鱼灬','火绳浸水','a215555921','V8娘_Official','zhr15216511265','Mr淋淋雨VG77','月魇夜',
                             'foo罗里达','格子迷妹','法克yui','淡是底色','剑桥大学']

        self.black_imghash = imagehash.hex_to_hash('33317161c161d9d9')
        self.nullhead_imghash = imagehash.hex_to_hash('2004b0617133f0c8')


    def quit(self):
        super(CloudReview,self).quit()


    @staticmethod
    def str2timestamp(_str:str):
        time_now = int(time.time())
        time_local = time.localtime(time_now)
        dt = time.strftime("%Y-%m-%d ",time_local)
        dt+=_str
        timeArray = time.strptime(dt, "%Y-%m-%d %H:%M")
        timestamp = time.mktime(timeArray)
        return timestamp


    def run_review(self):
        while self.cycle_times != 0:
            for thread in self._app_get_threads(self.tb_name):
                if self.__check_thread(thread):
                    self.log.info("Try to delete thread {title} post by {user_name}/{nick_name}".format(title=thread.title,user_name=thread.user_name,nick_name=thread.nick_name))
                    self._del_thread(self.tb_name,thread.tid)

            review_control = self._link_ctrl_json(self.ctrl_filepath)
            if review_control.get('quit_flag',False):
                self.log.debug("Quit the program controlled by cloud_review.json")
                return
            elif self.cycle_times >= 0:
                self.cycle_times-=1
            if self.sleep_time:
                time.sleep(self.sleep_time)
        self.log.debug("Quit the program controlled by cycle_times")


    def __check_text(self,obj,level=None):

        if obj.user_name in self.vz_white_list:
            return False

        if obj.user_name in ['罗清的指导','乐子投放机']:
            self.block({'tb_name':self.tb_name,
                        'user_name':obj.user_name,
                        'nick_name':obj.nick_name,
                        'portrait':obj.portrait,
                        'day':1})
            return True

        if self._mysql_search_pid(obj.pid):
            return False

        if type(obj) == browser.App_Thread:
            text = obj.title
        else:
            text = obj.text
            level = obj.level

        if level > 4:
            return False

        contact_exp = re.compile('(\+|加|联系|➕|＋|私|找).{0,2}(薇|微|wx|v|q|企鹅|❤|我)|(薇|微|wx|v|q|企鹅|❤).{0,2}(:|：|号)|q.?\d{6,11}|(d|滴)我|(私|s)(信|我|聊)|滴滴|dd|didi|有意.{0,3}(s|私)',re.I)

        has_white_kw = True if self.white_kw_exp.search(text) else False
        if level < 5:
            rare_kw_exp = re.compile('代骂服务|(高仿|复刻).{0,2}表|潮鞋|潮牌复刻|(实惠|羊毛).*群|撸货|线报|(手游|游戏)推广|福利号|手游.{0,2}招|仙侠游戏|游戏.{0,2}单|问卷调查|性腺|阳痿|早泄|蓝牙耳机|买.{0,3}车|出租|赛事预测|公司注册|有限公司|信用卡.*帮还|打苟桩|煮.{0,2}页|投.{0,2}像|点.?(像|象)头|页主|是时候给你们看下我的翅膀了|学互联网技术',re.I)
            if rare_kw_exp.search(text):
                if contact_exp.search(text):
                    self.block({'tb_name':self.tb_name,
                                'user_name':obj.user_name,
                                'nick_name':obj.nick_name,
                                'portrait':obj.portrait,
                                'day':10})
                    return True
                if level < 3 and not has_white_kw:
                    self.block({'tb_name':self.tb_name,
                                'user_name':obj.user_name,
                                'nick_name':obj.nick_name,
                                'portrait':obj.portrait,
                                'day':10})
                    return True

        if level < 4:
            maipian_exp = re.compile('(下|↓).{0,3}有惊喜|成人看的|小情侣|桌子上都是水|注意身体|推荐.{0,3}资源|回复.*:你(帖|贴).*可以看|自己上微.?薄|自己.*捜|都有.*看我关注的人|experience\+.{0,8}#.*#|看偏神器|遇见你6CS6|学姐给我吃|推荐发展对象|脱单|^麦片$|卖淫',re.I)
            if not has_white_kw and maipian_exp.search(text):
                if level < 3:
                    self.block({'tb_name':self.tb_name,
                                'user_name':obj.user_name,
                                'nick_name':obj.nick_name,
                                'portrait':obj.portrait,
                                'day':10})
                    return True
                if contact_exp.search(text):
                    self.block({'tb_name':self.tb_name,
                                'user_name':obj.user_name,
                                'nick_name':obj.nick_name,
                                'portrait':obj.portrait,
                                'day':10})
                    return True

        if level < 3:
            job_nocheck_exp = re.compile('想做单|抖音(点赞|任务)|拼夕夕.*点一下|助力微商|(淘宝|拼多多).{0,2}开店|淘tao寳|tb口令|养淘宝号|宝妈|跟着.{0,2}赚钱|免费入职|(招|收).{0,4}(临时工|短期工|徒)|(在家|轻松)(可|就能)做|时间自由|煎直|勉费|上迁.*没问题|迬页|#后期#.*做熟悉|连细方式|绿色正规行业|价格可谈',re.I)
            if job_nocheck_exp.search(text):
                self.block({'tb_name':self.tb_name,
                            'user_name':obj.user_name,
                            'nick_name':obj.nick_name,
                            'portrait':obj.portrait,
                            'day':10})
                return True
            job_exp = re.compile('兼职|声播|模特|陪玩|工作室|手工|项目|副业|代理|(免费|需要|诚信|诚心)(带|做)|想(赚|挣)钱|(刷|做)(单|销量)|微商|投资|拼dd|京d任务|不嫌少|需工作|拼多多|固定平台|号商',re.I)
            job_check_exp = re.compile('招|佣金|押金|日(结|洁)|高佣|想做的|有兴趣|稳赚|(一天|一日|每日|日进)\d{2,3}|(日|月)入.{0,2}(元|块|百|佰|万|w)|(利润|收益|工资|薪资)高|低风险|风险低|合作愉快',re.I)
            if not has_white_kw and job_exp.search(text) and (job_check_exp.search(text) or contact_exp.search(text)):
                self.block({'tb_name':self.tb_name,
                            'user_name':obj.user_name,
                            'nick_name':obj.nick_name,
                            'portrait':obj.portrait,
                            'day':10})
                return True
            course_exp = re.compile('摄影|视频(剪辑|特效)|后期|CAD|学习|素描|彩铅|板绘|绘画|设计|ps|美术|国画|水彩|领取.{0,3}课程|英语口语',re.I)
            course_check_exp = re.compile('群|课程|徒弟|素材|资料|教(程|学)|邮箱',re.I)
            if not has_white_kw and course_exp.search(text) and course_check_exp.search(text):
                self.block({'tb_name':self.tb_name,
                            'user_name':obj.user_name,
                            'nick_name':obj.nick_name,
                            'portrait':obj.portrait,
                            'day':10})
                return True

        if level == 1:
            female_exp = re.compile('仙女|小可爱|姐姐|软|萌|酥|娘|奶|喵|酱')
            if obj.gender == 1 and obj.nick_name and female_exp.search(obj.nick_name):
                female_check_exp = re.compile('聊天找我|女神|表姐|好孤单|男(朋|盆)友|睡不着|有兴趣|恋爱|宅女一枚|交友|老阿姨|爱情',re.I)
                if female_check_exp.search(obj.text) and not has_white_kw:
                    self.block({'tb_name':self.tb_name,
                                'user_name':obj.user_name,
                                'nick_name':obj.nick_name,
                                'portrait':obj.portrait,
                                'day':10})
                    return True

        return False


    def __check_thread(self,thread:browser.App_Thread):
        """
        检查thread内容
        """

        posts = self._app_get_posts(thread.tid,9999)[1]
        if posts:
            if posts[0].floor == 1 and thread.user_name not in self.vz_white_list:

                if self.__check_text(thread,posts[0].level):
                    return True

                if posts[0].level == 1 and thread.nick_name and re.match('贴吧用户_\w+$',thread.nick_name):
                    img_dhash = self._get_imgdhash('http://tb.himg.baidu.com/sys/portrait/item/' + thread.portrait)
                    if img_dhash:
                        if self.nullhead_imghash - img_dhash < 1:
                            return True
            for post in posts:
                flag = self.__check_post(post)
                if flag:
                    if post.floor == 1:
                        return True
                    else:
                        self.log.info("Try to delete post {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user_name,nick_name=post.nick_name))
                        self._del_post(self.tb_name,post.tid,post.pid)

        return False


    def __check_post(self,post:browser.App_Post):
        """
        检查回复内容
        """

        if self._mysql_search_pid(post.pid):
            return False

        if self.__check_text(post):
            return True

        if post.imgs:
            if not post.text and len(post.imgs) == 1 and post.nick_name and '缘园' in post.nick_name:
                img_dhash = self._get_imgdhash(post.imgs[0])
                if img_dhash:
                    if self.black_imghash - img_dhash < 1:
                        self.log.debug('大大滴好 in thread:{tid} floor:{floor}'.format(tid=post.tid,floor=post.floor))
                        return True
            if post.level < 4 and not self.white_kw_exp.search(post.text):
                for img in post.imgs:
                    if self._scan_QRcode(img):
                        self.block({'tb_name':self.tb_name,
                                    'user_name':post.user_name,
                                    'nick_name':post.nick_name,
                                    'portrait':post.portrait,
                                    'day':10})
                        return True

        self._mysql_add_pid(post.pid,post.portrait)
        return False
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan tieba threads')
    parser.add_argument('--review_ctrl_filepath','-rc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='path of the review control json | default value for example.py is ./user_control/example.json')
    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='path of the headers txt | default value is ./user_control/headers.txt')
    kwargs = vars(parser.parse_args())

    review = CloudReview(kwargs['header_filepath'],kwargs['review_ctrl_filepath'])
    review.run_review()
    review.quit()