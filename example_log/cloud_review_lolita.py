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

    def __check_thread(self,thread):
        """
        检查thread内容
        """
        if re.search(re.compile('python_test'),thread.topic):
            return True
        if re.search(re.compile('学.{0,6}(摄影|剪辑|后期|CAD|交流学习|素描|彩铅|板绘|绘画|设计)|招.{0,6}工'),thread.topic):
            self.block({'tb_name':self.tb_name,
                        'user_name':thread.user_name,
                        'nick_name':thread.nick_name,
                        'portrait':thread.portrait,
                        'day':10})
            return True

        flag = False
        posts = self._get_posts(thread.tid,9999)[1]
        for post in posts:
            if self.__check_post(post) == 1:
                self.log.info("Try to delete reply {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user_name,nick_name=post.nick_name))
                self._new_del_post(self.tb_name,post.tid,post.pid)
            elif self.__check_post(post) == 2:
                if posts[0].floor == 1 and post.user_name == posts[0].user_name:
                    self.block({'tb_name':self.tb_name,'user_name':post.user_name,'nick_name':post.nick_name,'portrait':post.portrait,'day':10})
                    flag = True
        if thread.reply_num > 30:
            posts = self._get_posts(thread.tid)[1]
            for post in posts:
                if self.__check_post(post) == 1:
                    self.log.info("Try to delete reply {text} post by {user_name}/{nick_name}".format(text=post.text,user_name=post.user_name,nick_name=post.nick_name))
                    self._new_del_post(self.tb_name,post.tid,post.pid)
                elif self.__check_post(post) == 2:
                    if posts[0].floor == 1 and post.user_name == posts[0].user_name:
                        self.block({'tb_name':self.tb_name,'user_name':post.user_name,'nick_name':post.nick_name,'portrait':post.portrait,'day':10})
                        flag = True
        return flag

    def __check_post(self,post):
        """
        检查回复内容
        """
        if post.level > 11:
            return 0
        if post.level == 1 and post.floor == 1:
            return 1
        re_list = ['(ps|PS|Ps).*(素材|资料)','(摄影|剪辑|后期|CAD|交流学习|素描|彩铅|板绘|绘画|设计).*(群|课|徒)','小红娘[\s\S]*单身','(小姐姐|jk|lo娘|女.?友|对象).*(长期|资助|包养|养你)','代购[\s\S]*薅羊毛','(资助|包养).*(小姐姐|jk|lo娘|女.?友|对象)','招.*(主播|主持|兼职)','手游[\s\S]*下载','在家工作.*自由','(唱歌|声音)好听.*小(哥|姐)','(淘宝|天猫|京东).*(内部优惠|线报|漏洞)','学习资料']
        if post.level < 12 and re.search(re.compile('|'.join(re_list),re.I),post.text):
            self.block({'tb_name':self.tb_name,
                        'user_name':post.user_name,
                        'nick_name':post.nick_name,
                        'portrait':post.portrait,
                        'day':10})
            return 1
        if post.level<8 and len(post.text)<25 and re.search(re.compile('线下|dd|私',re.I),post.text):
            if re.search(re.compile('小可爱|小姐姐|lo娘|仙女',re.I),post.text):
                self.block({'tb_name':self.tb_name,
                            'user_name':post.user_name,
                            'nick_name':post.nick_name,
                            'portrait':post.portrait,
                            'day':10})
        if re.search(re.compile('@(小度🎁活动🔥|小度º活动君|活动🔥小度🎁)|简单，.*看.*发.*帖'),post.text):
            return 2
        black_list = ['a3383567a','Kether76','我是小女孩阿']
        if post.user_name in black_list:
            return 1
        if post.imgs and post.level < 8 and not re.search(re.compile('挂人|避雷|姐妹|裙|同好|lo娘',re.I),post.text):
            if not self._mysql_search_pid(post.pid):
                for img in post.imgs:
                    if self._scan_QRcode(img):
                        self.block({'tb_name':self.tb_name,
                                    'user_name':post.user_name,
                                    'nick_name':post.nick_name,
                                    'portrait':post.portrait,
                                    'day':10})
                        return 1
                self._mysql_add_pid(post.pid)

        return 0

    def run_review(self):
        while self.cycle_times != 0:
            for pn in range(0,100,50):
                print(pn)
                threads = self._get_threads(self.tb_name,pn)
                for thread in threads:
                    if self.__check_thread(thread):
                        self.log.info("Try to delete thread {topic} post by {user_name}/{nick_name}".format(topic=thread.topic,user_name=thread.user_name,nick_name=thread.nick_name))
                        self._new_del_thread(self.tb_name,thread.tid)

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