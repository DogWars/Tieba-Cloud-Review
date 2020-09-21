#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
2020-09-15 更新
1、考虑到v吧极高的扫描频率，现已删去大部分封禁相关语句，避免误封
2、改用公共正则表达式
3、适配更新后的MySQL调用api，将黑白名单查询简化合并为一次fetch
"""
import os
import sys
import time
import argparse

import re
import browser

import imagehash



PATH = os.path.split(os.path.realpath(__file__))[0]



class CloudReview(browser.CloudReview):


    __slots__ = ('white_kw_exp',
                 'black_imghash',
                 'nullhead_imghash')


    def __init__(self,headers_filepath,ctrl_filepath):
        super(CloudReview,self).__init__(headers_filepath,ctrl_filepath)

        white_kw_list = ['vup|vtb|vtuber|管人|(几个|哪个|什么|的)v',
                         '(a|b|睿|皇协|批|p)站|海鲜|v吧|v8|nga|404|油管|ytb|油土鳖|论坛|字幕组|粉丝群',
                         '4v|樱花妹|中之人|国v|个人势|holo|虹|🌈|2434|杏|vr|木口|猴楼|大家庭|皮套|纸片人|套皮|主播',
                         '😅|👿|🐜|🤡|🏃|🐮|😨|👅|🐭|🐌',
                         '配信|联动|歌回|台词回|杂谈|歌力|企划|隐退|转生|复活|前世|sc|弹幕|二次元|开播|取关',
                         '如何评价|不懂就问|大的来了|很喜欢|我命令|速来|啊这|麻了|az|sj|懂.都懂|懂完了|太懂|4d|dddd|yyds|cylx|搁这|冲冲冲|反串|缝合|太嗯|不用.?多说了吧|拿下|我们.*真是太|可不敢|乱说|细说|谜语|拉胯|虚无|牛(大了|的)|真不熟|成分|黑屁|破防|真可怜|发病|开团|(好|烂)活|干碎|对线|整活|批爆|乐了|乐子|橄榄|罢了|确实|可爱|芜湖|钓鱼|梁木|节奏|冲锋|yygq|芜狐|不如意|直播间|别尬|离谱|天使|母人|阴间|这波|泪目|图一乐',
                         '懂哥|孝子|蛆|(大|带)(伙|🔥)|xdm|懂哥|mmr|萌萌人|gachi|anti|粉丝|太监|天狗|利普贝当|crew|杏奴|贵物|沙口|小鬼|后浪|人(↑|上)人|仌|鼠人','爬|爪巴|滚|gck|有病吧|nt|啥卵']
        self.white_kw_exp = re.compile('|'.join(white_kw_list),re.I)

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
            for thread in self.get_threads(self.tb_name):
                if self.__check_thread(thread):
                    browser.log.info("Try to delete thread {title} post by {user_name}/{nick_name}".format(title=thread.text,user_name=thread.user.user_name,nick_name=thread.user.nick_name))
                    self.del_thread(self.tb_name,thread.tid)

            review_control = self._link_ctrl_json(self.ctrl_filepath)
            if review_control.get('quit_flag',False):
                browser.log.debug("Quit the program controlled by cloud_review.json")
                return
            elif self.cycle_times >= 0:
                self.cycle_times-=1
            if self.sleep_time:
                time.sleep(self.sleep_time)
        browser.log.debug("Quit the program controlled by cycle_times")


    def __check_text(self,obj,level = None):

        if self.mysql_has_pid(obj.pid):
            return -1

        is_white = self.mysql_iswhite_portrait(obj.user.portrait)
        if is_white == True:
            return -1
        elif is_white == False:
            self.block(obj.user,self.tb_name,day=1)
            return 1
        else:
            pass

        if type(obj) == browser.Thread:
            pass
        else:
            level = obj.level

        if level > 4:
            return -1

        text = obj.text

        has_rare_contact = True if self.exp.contact_rare_exp.search(text) else False
        has_contact = True if (has_rare_contact or self.exp.contact_exp.search(text)) else False
        has_white_kw = True if self.white_kw_exp.search(text) else False

        if level < 5:
            if self.exp.job_nocheck_exp.search(text):
                return 1
            if self.exp.app_nocheck_exp.search(text):
                return 1

        if level < 4:
            if not has_white_kw and self.exp.maipian_exp.search(text):
                if level < 3:
                    return 1
                if has_contact:
                    return 1
            if obj.user.gender == 2:
                if not has_white_kw and self.exp.female_check_exp.search(text):
                    return 1
                if obj.has_audio:
                    return 1

        if level < 3:
            if self.exp.business_exp.search(text):
                return 1
            if not has_white_kw:
                if self.exp.job_exp.search(text) and (self.exp.job_check_exp.search(text) or has_contact):
                    return 1
                if self.exp.app_exp.search(text) and (self.exp.app_check_exp.search(text) or has_contact):
                    return 1
                if self.exp.course_exp.search(text) and self.exp.course_check_exp.search(text):
                    return 1
                if self.exp.game_exp.search(text):
                    return 1

        if level == 1:
            if obj.user.user_name:
                if self.exp.name_nocheck_exp.search(obj.user.user_name):
                    return 1
                if self.exp.name_exp.search(obj.user.user_name) and not has_white_kw:
                    if self.exp.name_check_exp.search(obj.user.user_name) or has_contact:
                        return 1
            if obj.user.nick_name:
                if self.exp.name_nocheck_exp.search(obj.user.nick_name):
                    return 1
                if self.exp.name_exp.search(obj.user.nick_name) and not has_white_kw:
                    if self.exp.name_check_exp.search(obj.user.nick_name) or has_contact:
                        return 1
            if self.exp.lv1_exp.search(text):
                return 1
            if not has_white_kw and self.exp.contact_rare_exp.search(text):
                return 1

        return 0


    def __check_thread(self,thread:browser.Thread):
        """
        检查thread内容
        """

        posts = self.get_posts(thread.tid,9999)[1]
        if posts and posts[0].floor == 1:
            level = posts[0].level
            flag = self.__check_text(thread,level)
            if flag == -1:
                pass
            elif flag == 1:
                return True
            elif flag == 0:
                pass
            else:
                browser.log.error('Wrong flag {flag} in __check_thread!'.format(flag=flag))
                pass

        for post in posts:
            flag = self.__check_post(post)
            if flag == 0:
                pass
            elif flag == 1:
                if post.floor == 1:
                    return True
                else:
                    browser.log.info("Try to delete post {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user.user_name,nick_name=post.user.nick_name))
                    self.del_post(self.tb_name,post.tid,post.pid)
            elif flag == 2:
                return True
            else:
                browser.log.error('Wrong flag {flag} in __check_thread!'.format(flag=flag))

        return False


    def __check_post(self,post:browser.Post):
        """
        检查回复内容
        """

        flag = self.__check_text(post)
        if flag == -1:
            return 0
        elif flag == 1:
            return 1
        elif flag == 0:
            if post.is_thread_owner and post.level < 4 and self.exp.kill_thread_exp.search(post.text):
                return 2

            if post.imgs:
                if post.level < 4 and not self.white_kw_exp.search(post.text):
                    for img in post.imgs:
                        url = self._scan_QRcode(img)
                        if url and url.startswith('http'):
                            return 1
        else:
            browser.log.error('Wrong flag {flag} in __check_post!'.format(flag=flag))

        self.mysql_add_pid(post.pid,post.user.portrait)
        return 0
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan tieba threads',allow_abbrev=False)
    parser.add_argument('--review_ctrl_filepath','-rc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='review_control.json的路径，对example.py而言默认值为./user_control/example.json')
    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='headers.txt（包含BDUSS的消息头）的路径，默认值为./user_control/headers.txt')
    args = parser.parse_args()

    review = CloudReview(args.header_filepath,args.review_ctrl_filepath)
    review.run_review()
    review.quit()