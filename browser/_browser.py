#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('_Browser','_Thread','_Post','_Comment','SCRIPT_PATH','FILENAME','SHOTNAME')

import os
import sys
import time
import logging
from functools import wraps

import hashlib

import requests as req

import re
import json
import html
import pickle
from bs4 import BeautifulSoup


PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')
SCRIPT_PATH,FILENAME = os.path.split(os.path.realpath(sys.argv[0]))
SCRIPT_PATH = SCRIPT_PATH.replace('\\','/')
SHOTNAME = os.path.splitext(FILENAME)[0]


class _Thread():
    """
    主题帖信息

    tid:帖子编号
    pid:回复编号
    topic:标题
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    reply_num:回复数
    """

    __slots__ = ('tid',
                 'pid',
                 'topic',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'reply_num')

    def __init__(self):
        pass


class _Post():
    """
    楼层信息

    text:正文
    tid:帖子编号
    pid:回复编号
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    level:用户等级
    floor:楼层数
    comment_num:楼中楼回复数
    sign:签名照片
    imgs:图片列表
    smileys:表情列表
    """

    __slots__ = ('text',
                 'tid',
                 'pid',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'level',
                 'floor',
                 'is_thread_owner',
                 'comment_num',
                 'sign',
                 'imgs',
                 'smileys')

    def __init__(self):
        pass


class _Comment():
    """
    楼中楼信息

    text:正文
    tid:帖子编号
    pid:回复编号
    user_name:发帖用户名
    nick_name:发帖人昵称
    portrait:用户头像portrait值
    smileys:表情列表
    """

    __slots__ = ('text',
                 'tid',
                 'pid',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'smileys')

    def __init__(self):
        pass


class _Headers():
    """
    消息头
    """

    __slots__ = ('headers','cookies')

    def __init__(self,filepath):
        self.update(filepath)

    def update(self,filepath:str):
        """
        Read headers.txt and return the dict of headers.
        read_headers_file(filepath)

        Parameters:
            filepath:str Path of the headers.txt
        """
        self.headers = {}
        self.cookies = {}
        try:
            with open(filepath,'r',encoding='utf-8') as header_file:
                rd_lines = header_file.readlines()
                for text in rd_lines:
                    text = text.replace('\n','').split(':',1)
                    self.headers[text[0].strip()] = text[1].strip()
        except(FileExistsError):
            raise(FileExistsError('headers.txt not exist! Please create it from browser!'))

        if self.headers.__contains__('Referer'):
            del self.headers['Referer']
        if self.headers.__contains__('Cookie'):
            for text in self.headers['Cookie'].split(';'):
                text = text.strip().split('=')
                self.cookies[text[0]] = text[1]
        else:
            raise(AttributeError('raw_headers["cookies"] not found!'))


class _Browser():
    """
    贴吧浏览、参数获取等API的封装
    _Browser(headers_filepath:str)
    """
    tieba_url = 'http://tieba.baidu.com/f'
    tieba_post_url = 'http://tieba.baidu.com/p/'
    comment_url = 'http://tieba.baidu.com/p/comment'
    user_homepage_url = 'https://tieba.baidu.com/home/main/'

    tbs_api = 'http://tieba.baidu.com/dc/common/tbs'
    fid_api = 'http://tieba.baidu.com/sign/info'
    user_json_api = 'http://tieba.baidu.com/i/sys/user_json'
    panel_api = 'https://tieba.baidu.com/home/get/panel'
    self_info_api = 'http://tieba.baidu.com/f/user/json_userinfo'


    def __init__(self,headers_filepath:str):
        """
        _Browser(headers_filepath:str)
        """

        if not os.path.exists(PATH + '/log'):
            os.mkdir(PATH + '/log')
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        log_filepath = ''.join([PATH,'/log/',SHOTNAME.upper(),'_',recent_time,'.log'])
        try:
            file_handler = logging.FileHandler(log_filepath,encoding='utf-8')
        except(PermissionError):
            try:
                os.remove(log_filepath)
            except(OSError):
                raise(OSError('''Can't write and remove {path}'''.format(path=log_filepath)))
            else:
                file_handler = logging.FileHandler(log_filepath,encoding='utf-8')

        formatter = logging.Formatter("<%(asctime)s> [%(levelname)s]  %(message)s","%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        self.log = logging.getLogger(__name__)
        self.log.addHandler(file_handler)
        self.log.setLevel(logging.INFO)

        self.fid_cache_filepath = PATH + '/cache/fid_cache.pk'
        try:
            with open(self.fid_cache_filepath,'rb') as pickle_file:
                self.fid_dict = pickle.load(pickle_file)
        except(FileNotFoundError,EOFError):
            self.log.warning('"{filepath}" not found. Create new fid_dict'.format(filepath=self.fid_cache_filepath))
            self.fid_dict = {}

        self.account = _Headers(headers_filepath)


    def quit(self):
        """
        自动缓存fid信息
        """
        try:
            with open(self.fid_cache_filepath,'wb') as pickle_file:
                pickle.dump(self.fid_dict,pickle_file)
        except AttributeError:
            self.log.warning("Failed to save fid cache!")


    @staticmethod
    def _is_nick_name(name:str):
        name = str(name)
        return True if re.search('^[\u4e00-\u9fa5\w]',name) else False


    def _is_vip(self,keyword:str):
        if keyword.startswith('tb.'):
            params = {'id':keyword}
        else:
            params = {'un':keyword}

        self._set_host(self.panel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.panel_api,
                              params=params,
                              headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    break
            retry_times-=1
            time.sleep(0.25)

        if res.status_code == 200:
            if re.search('"vipInfo":\[\]',res.text):
                return False
            else:
                return True
        else:
            self.log.warning('Failed to get vip status of {keyword}!'.format(keyword=keyword))
            return None


    def _is_self_vip(self):
        self._set_host(self.self_info_api)
        portrait = None
        retry_times = 2
        while retry_times:
            try:
                res = req.get(self.self_info_api,
                              headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"user_portrait":"([\w.-]+)',res.text)
                    if raw:
                        portrait = raw.group(1)
                        break
            retry_times-=1
            time.sleep(0.25)

        if not portrait:
            self.log.error("Failed to get self info")
            return None

        return self._is_vip(portrait)


    def _set_host(self,url:str):
        try:
            self.account.headers['Host'] = re.search('://(.+?)/',url).group(1)
        except AttributeError:
            self.log.warning('Wrong type of url "{url}"!'.format(url=url))


    def _get_tbs(self):
        self._set_host(self.tbs_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.get(self.tbs_api,
                              headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"tbs":"([a-z\d]+)',res.text)
                    if raw:
                        tbs = raw.group(1)
                        return tbs
            retry_times-=1
            time.sleep(0.25)

        self.log.error("Failed to get tbs")
        return ''


    def _get_fid(self,tb_name:str):
        if self.fid_dict.__contains__(tb_name):
            return self.fid_dict[tb_name]
        else:
            self._set_host(self.fid_api)
            retry_times = 10
            while retry_times:
                try:
                    res = req.get(self.fid_api,
                                  params={'kw':tb_name,'ie':'utf-8'},
                                  headers = self.account.headers)
                except(req.exceptions.RequestException):
                    pass
                else:
                    if res.status_code == 200:
                        raw = re.search('"forum_id":(\d+)', res.text)
                        if raw:
                            fid = raw.group(1)
                            self.fid_dict[tb_name] = fid
                            return fid
                retry_times-=1
                time.sleep(0.5)

        self.log.critical("Failed to get fid of {name}".format(name=tb_name))
        raise(ValueError("Failed to get fid of {name}".format(name=tb_name)))


    def _get_sign(self,data):
        raw_list = []
        for key,value in data.items():
            raw_list.extend([key,'=',str(value)])
        raw_str = ''.join(raw_list) + 'tiebaclient!!!'
        md5 = hashlib.md5()
        md5.update(raw_str.encode('utf-8'))
        sign = md5.hexdigest().upper()
        return sign


    def _get_portrait(self,name:str):
        name = str(name)
        if not self._is_nick_name(name):
            self._set_host(self.user_json_api)
            retry_times = 2
            while retry_times:
                try:
                    res = req.get(self.user_homepage_url,
                                  params={'un':name},
                                  headers=self.account.headers).text
                except(req.exceptions.RequestException):
                    pass
                else:
                    if res.status_code == 200:
                        raw = re.search('"portrait":"([\w.-]+)', res.text)
                        if raw:
                            portrait = raw.group(1)
                            return portrait
                retry_times-=1

        self._set_host(self.panel_api)
        retry_times = 2
        while retry_times:
            try:
                res = req.get(self.panel_api,
                              params={'un':name},
                              headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"portrait":"([\w.-]+)', res.text)
                    if raw:
                        portrait = raw.group(1)
                        return portrait
            retry_times-=1

        self.log.error("Failed to get portrait of {name}".format(name=name))
        return ''


    def _get_user_id(self,name:str):
        name = str(name)
        if not self._is_nick_name(name):
            self._set_host(self.user_json_api)
            retry_times = 2
            while retry_times:
                try:
                    res = req.get(self.user_homepage_url,
                                  params={'un':name},
                                  headers=self.account.headers)
                except(req.exceptions.RequestException):
                    pass
                else:
                    if res.status_code == 200:
                        raw = re.search('"id":(\d+)', res.text)
                        if raw:
                            user_id = raw.group(1)
                            return user_id
                retry_times-=1

        self._set_host(self.panel_api)
        retry_times = 2
        while retry_times:
            try:
                res = req.get(self.panel_api,
                              params={'un':name},
                              headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"id":(\d+)', res.text)
                    if raw:
                        user_id = raw.group(1)
                        return user_id
            retry_times-=1

        self.log.error("Failed to get user_id of {name}".format(name=name))
        return ''


    def _get_threads(self,tb_name,pn=0):
        """
        获取首页帖子
        _get_threads(tb_name,pn=0)

        Returns:
            _Thread
        """

        threads = []
        self._set_host(self.tieba_url)
        raws = []
        retry_times = 20
        while retry_times:
            try:
                res = req.get(self.tieba_url,
                              params={'kw':tb_name,'pn':pn,'ie':'utf-8'},
                              headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raws = re.findall('thread_list clearfix([\s\S]*?)创建时间"',html.unescape(res.text))
                    if raws:
                        break
            retry_times-=1
            time.sleep(0.5)

        if not raws:
            self.log.error("Failed to get threads in {tb_name}!".format(tb_name=tb_name))
            return threads

        for raw in raws:
            try:
                thread = _Thread()
                thread.tid = int(re.search('href="/p/(\d*)', raw).group(1))
                thread.pid = re.search('"first_post_id":(.*?),', raw).group(1)
                thread.topic = html.unescape(re.search('href="/p/.*?" title="([\s\S]*?)"', raw).group(1))
                thread.reply_num = int(re.search('"reply_num":(.*?),',raw).group(1))
                thread.user_name = re.search('''frs-author-name-wrap"><a rel="noreferrer"  data-field='{"un":"(.*?)",''',raw).group(1).encode('utf-8').decode('unicode_escape')
                thread.nick_name = re.search('title="主题作者: (.*?)"', raw).group(1)
                thread.portrait = re.search('id":"(.*?)"}',raw).group(1)
            except(AttributeError):
                continue
            else:
                threads.append(thread)

        return threads


    def _get_posts(self,tid,pn=1):
        """
        获取帖子回复
        _get_post(tid,pn=1)

        Returns:
            has_next: 是否还有下一页
            _Post
        """

        self._set_host(self.tieba_post_url)

        raw = None
        retry_times = 20
        while retry_times:
            try:
                res = req.get(self.tieba_post_url + str(tid),
                              params={'pn':pn},
                              headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('<div class="p_postlist" id="j_p_postlist">.*</div>',res.text,re.S)
                    if raw:
                        raw = raw.group()
                        break
            retry_times-=1
            time.sleep(0.5)

        if not raw:
            self.log.error("Failed to get posts of {tid}".format(tid=tid))
            return False,[]

        has_next = True if re.search('<a href=".*">尾页</a>',raw) else False
        content = BeautifulSoup(raw,'lxml')
        post_list = []
        try:
            posts = content.find_all("div",{'data-field':True,'data-pid':True})
            for post_raw in posts:
                post = _Post()
                post.tid = tid

                text_raw = post_raw.find("div",id=re.compile('^post_content_\d+$'))
                post.text = ''.join(text_raw.strings).strip()

                user_sign = post_raw.find(class_='j_user_sign')
                if user_sign:
                    post.sign = user_sign["src"]
                else:
                    post.sign = None

                imgs_raw = text_raw.find_all("img",class_='BDE_Image')
                post.imgs = [i["src"] for i in imgs_raw]

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                post.smileys = [i["src"] for i in smileys_raw]

                post.is_thread_owner = True if post_raw.find("div",class_=re.compile('^louzhubiaoshi')) else False

                author_info = json.loads(post_raw["data-field"])
                post.pid = author_info["content"]["post_id"]
                post.user_name = author_info["author"]["user_name"]
                post.nick_name = author_info["author"]["user_nickname"]
                post.portrait = re.search('[^?]*',author_info["author"]["portrait"]).group()
                post.level = int(post_raw.find('div',attrs={'class':'d_badge_lv'}).text)
                post.floor = int(author_info["content"]["post_no"])
                post.comment_num = int(author_info["content"]["comment_num"])

                post_list.append(post)

        except KeyError:
            self.log.error("KeyError: Failed to get posts of {tid}".format(tid=tid))
            return False,[]
        else:
            return has_next,post_list


    def _get_comments(self,tid,pid,pn=1):
        """
        获取楼中楼回复
        _get_comment(tid,pid,pn=1)

        Returns:
            has_next: 是否还有下一页
            _Comment
        """   
        
        self._set_host(self.comment_url)
        retry_times = 20
        while retry_times:
            try:
                res = req.get(self.comment_url,
                              params={'tid':tid,'pid':pid,'pn':pn},
                              headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0.5)

        if not raw:
            self.log.error("Failed to get comments of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return False,[]

        content = BeautifulSoup(res.text,'lxml')
        comments = []
        try:
            raws = content.find_all('li',class_=re.compile('^lzl_single_post'))
            has_next = True if content.find('a',string='下一页') else False

            for comment_raw in raws:
                comment = _Comment()
                comment_data = json.loads(comment_raw['data-field'])
                comment.tid = tid
                comment.pid = comment_data['spid']
                comment.portrait = comment_data['portrait']
                comment.user_name = comment_data['user_name']
                nick_name = comment_raw.find('a',class_='at j_user_card').text
                if nick_name == comment.user_name:
                    comment.nick_name = ''
                else:
                    comment.nick_name = nick_name

                text_raw = comment_raw.find('span',class_='lzl_content_main')
                comment.text = text_raw.text.strip()

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                comment.smileys = [i["src"] for i in smileys_raw]

                comments.append(comment)

            return has_next,comments

        except KeyError:
            log.error("KeyError: Failed to get posts of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return False,[]