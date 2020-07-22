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


    def __check_thread(self,thread:browser._App_Thread):
        """
        检查thread内容
        """
        if re.search(re.compile('python_test|我发表了一篇图片贴|分享.*创建的歌单|刚申请.*音乐人|拼.{0,5}会员|拼团|微信.*群'),thread.title):
            return True
        if re.search(re.compile('招.*主播|新平台.*好播'),thread.title):
            self.block({'tb_name':self.tb_name,
                        'user_name':thread.user_name,
                        'nick_name':thread.nick_name,
                        'portrait':thread.portrait,
                        'day':10})
            return True

        posts = self._app_get_posts(thread.tid,9999)[1]
        if posts and posts[0].floor == 1 and posts[0].level < 7:
            huguan_exp = re.compile('互关|互粉|互吗|选互|选关$|】互$|分享.{0,10}创建的歌单|刚申请.{0,10}音乐人|拼.{0,5}会员|微信.{0,10}群|http://music\.163\.com/artist')
            if re.search(huguan_exp,thread.title) or re.search(huguan_exp,posts[0].text):
                return True
            listen_together_exp = re.compile('一起听|来听歌|一起网(易|抑)(云|☁)')
            if posts[0].level == 1:
                if re.search(listen_together_exp,thread.title) or re.search(listen_together_exp,posts[0].text):
                    if re.search(re.compile('怎|哪|何|啥|问'),thread.title):
                        return False
                    else:
                        return True
        if posts and posts[0].floor == 1 and posts[0].level < 3 and not posts[0].imgs and len(posts[0].text) < 12 and len(thread.title) < 9:
            return True
        for post in posts:
            if self.__check_post(post):
                self.log.info("Try to delete reply {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user_name,nick_name=post.nick_name))
                self._del_post(self.tb_name,post.tid,post.pid)
        return False


    def __check_post(self,post:browser._App_Post):
        """
        检查回复内容
        """
        white_list = ['米珞','kk不好玩','gxc射手94','一生爱自由_','我的查查呢','丶柚凉天','依币guy','做个坏先生']
        if post.user_name in white_list:
            return False
        black_list = ['出差vv就','二档之路飞','姑苏宅仔','戰誏琇纔','是酥酥鸭mm','collectors蛇叔','Perish妍','做个坏先生','武汉大帅哥呀哈','苍桑文墨','鬼子扛枪993','夏天Yenjoy','906013350qq']
        if post.user_name in black_list:
            return True
        if re.search(re.compile('狐臭|公会|工作室|(唱歌|声音)好听.{0,10}小(哥|姐)|QVE.{0,10}软件|华强北.{0,10}airpods',re.I),post.text) and post.level < 11:
            self.block({'tb_name':self.tb_name,
                        'user_name':post.user_name,
                        'nick_name':post.nick_name,
                        'portrait':post.portrait,
                        'day':10})
            return True
        if re.search(re.compile('暑假工|临时工|兼职|主播|声播|主持|模特|陪玩|手游|礼物|底薪',re.I),post.text) and post.level < 8:
            if post.level < 4:
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
                return True
            if re.search(re.compile('招|聘|收',re.I),post.text):
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
                return True
        if re.search(re.compile('业务|上榜|推广|刷级|刷听歌|听歌量|接单|粉丝|等级|评论|点赞|飙升榜|黑胶|会员|爱奇艺|优酷|音乐人|达人|歌曲入库|认证|刷单|混音|编曲|作曲|作词|播放|下架|(300|三百)首',re.I),post.text) and post.level < 4:
            if re.search(re.compile('业务|联系|找我|私|滴滴|dd|(有|无)偿|免费|代充|低价|(帮|代).{0,1}(办|申请|过|刷)|(\+|加|联系|➕|＋).{0,2}(薇|微|v|q|企鹅)|秒听|网站|公众号',re.I),post.text):
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
                return True
        if re.search(re.compile('摄影|剪辑|后期|CAD|学习|素描|彩铅|板绘|绘画|设计|ps|美术|国画|水彩',re.I),post.text) and post.level < 5:
            if re.search(re.compile('群|课|徒|素材|资料|教程|学习',re.I),post.text):
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
                return True

        if re.search(re.compile('(出|收)[\s\S]{0,12}(会员|黑胶|级号|年卡|账号)|联系方式'),post.text) and post.level < 7:
            self.block({'tb_name':self.tb_name,
                        'user_name':post.user_name,
                        'nick_name':post.nick_name,
                        'portrait':post.portrait,
                        'day':1})
            return True
        if post.imgs:
            if not self._mysql_search_pid(post.pid):
                for img in post.imgs:
                    if self._scan_QRcode(img):
                        self.block({'tb_name':self.tb_name,
                                    'user_name':post.user_name,
                                    'nick_name':post.nick_name,
                                    'portrait':post.portrait,
                                    'day':1})
                        return True
                self._mysql_add_pid(post.pid)

        return False


    def run_review(self):
        while self.cycle_times != 0:
            threads = self._app_get_threads(self.tb_name)
            for thread in threads:
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