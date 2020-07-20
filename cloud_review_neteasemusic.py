#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

import re
import browser

PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

class CloudReview(browser._CloudReview):
    def __init__(self,raw_headers,ctrl_filepath):
        super(CloudReview,self).__init__(raw_headers,ctrl_filepath)

    def quit(self):
        super(CloudReview,self).quit()

    def __check_thread(self,thread:browser._Thread):
        """
        检查thread内容
        """
        if re.search(re.compile('python_test|我发表了一篇图片贴|分享.*创建的歌单|刚申请.*音乐人|拼.{0,5}会员|拼团|微信.*群'),thread.topic):
            return True
        if re.search(re.compile('爱奇艺|优酷|大会员'),thread.topic):
            self.block({'tb_name':self.tb_name,
                        'user_name':thread.user_name,
                        'nick_name':thread.nick_name,
                        'portrait':thread.portrait,
                        'day':3})
            return True
        if re.search(re.compile('招.*主播'),thread.topic):
            self.block({'tb_name':self.tb_name,
                        'user_name':thread.user_name,
                        'nick_name':thread.nick_name,
                        'portrait':thread.portrait,
                        'day':10})
            return True

        posts = self._get_posts(thread.tid,9999)[1]
        if posts and posts[0].floor == 1 and posts[0].level < 7 and re.search(re.compile('互关|互粉|互吗|选互|选关$|】互$'),thread.topic):
            return True
        if posts and posts[0].floor == 1 and posts[0].level == 1 and re.search(re.compile('一起听|来听歌|一起网(易|抑)(云|☁)'),thread.topic):
            if re.search(re.compile('怎|哪|何|啥|问'),thread.topic):
                return False
            else:
                return True
        if posts and posts[0].floor == 1 and posts[0].level < 5 and not posts[0].imgs and len(posts[0].text) < 9 and len(thread.topic) < 15:
            return True
        for post in posts:
            if self.__check_post(post):
                self.log.info("Try to delete reply {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user_name,nick_name=post.nick_name))
                self._del_post(self.tb_name,post.tid,post.pid)
        return False

    def __check_post(self,post:browser._Post):
        """
        检查回复内容
        """
        white_list = ['米珞','kk不好玩','gxc射手94','一生爱自由_','我的查查呢','丶柚凉天','依币guy','做个坏先生']
        if post.user_name in white_list:
            return False
        black_list = ['出差vv就','二档之路飞','姑苏宅仔','戰誏琇纔','是酥酥鸭mm','collectors蛇叔','Perish妍','做个坏先生','武汉大帅哥呀哈','想吹风吗','苍桑文墨','鬼子扛枪993']
        if post.user_name in black_list:
            return True
        re_list = ['(招|聘|收).{0,8}(暑假工|临时工|兼职|主播|声播|主持|模特|陪玩|代理)','网易云(业务|上榜|推广)','有偿接单','(摄影|剪辑|后期|CAD|交流学习|素描|彩铅|板绘|绘画|设计|ps|美术|国画|水彩)[\s\S]{0,20}(群|课|徒|素材|资料|教程|学习)','手游','音乐推广','(有意|要的)(私|留言|滴滴|dd)','低价.{0,10}(黑胶|会员)','(黑胶|会员).{0,10}代充','刷.?(粉丝|等级|评论|点赞|日推|飙升榜)','(粉丝|等级|评论|点赞|日推|飙升榜).{0,10}(价)','(接).{0,10}(音乐人|达人)','(帮|代).{0,10}(办|申请|过).{0,10}(音乐人|达人|私)','(音乐人|达人).{0,10}(帮|代).{0,10}(办|申请|过)','歌曲入库','音乐认证','收.{0,10}礼物','刷单','狐臭','公会','工作室','招.{0,10}主播','(唱歌|声音)好听.{0,10}小(哥|姐)','(混音|编曲|作曲|作词|点赞|粉丝|播放|下架).{0,10}(私|业务|联系|找我)','兼职','底薪','闲鱼','(\+|加|联系|➕|＋).{0,2}(薇|微|v|q|企鹅)','学习资料','绘画','QVE.{0,10}软件','(刷|秒听).{0,10}(300|三百)首','听歌量.{0,10}网站','公众号','(会员|黑胶).{0,10}年\d{2,3}','华强北.{0,10}airpods']
        if re.search(re.compile('|'.join(re_list),re.I),post.text) and post.level < 5:
            self.block({'tb_name':self.tb_name,
                        'user_name':post.user_name,
                        'nick_name':post.nick_name,
                        'portrait':post.portrait,
                        'day':10})
            return True
        if re.search(re.compile('(出|收)[\s\S]{0,12}(会员|黑胶|级号|年卡|账号)|联系方式'),post.text) and post.level < 10:
            self.block({'tb_name':self.tb_name,
                        'user_name':post.user_name,
                        'nick_name':post.nick_name,
                        'portrait':post.portrait,
                        'day':1})
            return True
        if  post.floor == 1 and post.level < 7 and re.search(re.compile('互关|互粉|互吗\Z|\A互\Z|\A选互|\A选关|分享.{0,10}创建的歌单|刚申请.{0,10}音乐人|拼.{0,5}会员|微信.{0,10}群|http://music\.163\.com/artist'),post.text):
            return True
        if post.nick_name:
            if re.search(re.compile('小奶猫|小母猫|雅雅.?姐|奶.?喵|猫咪.[A-Z]|蜜桃花开|^..[A-Z]大奶猫.$|^浅夏.{3}[A-Z]$|^.清[A-Z]澄..$|^芊芊..[A-Z].$|^倾城.{4}$|^[A-Z]花.落..$'),post.nick_name) and post.level < 3:
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
                return True
        if post.imgs:
            if not self._mysql_search_pid(post.pid):
                for img in post.imgs:
                    if self._scan_QRcode(img):
                        self.block({'tb_name':self.tb_name,
                                    'user_name':post.user_name,
                                    'nick_name':post.nick_name,
                                    'portrait':post.portrait,
                                    'day':10})
                        return True
                self._mysql_add_pid(post.pid)

        return False

    def run_review(self):
        while self.cycle_times != 0:
            threads = self._get_threads(self.tb_name)
            for thread in threads:
                if self.__check_thread(thread):
                    self.log.info("Try to delete thread {topic} post by {user_name}/{nick_name}".format(topic=thread.topic,user_name=thread.user_name,nick_name=thread.nick_name))
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