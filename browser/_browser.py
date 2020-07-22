#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('_Browser',
           '_Web_Thread',
           '_Web_Post',
           '_Web_Comment',
           '_App_Thread',
           '_App_Post',
           '_App_Comment',
           'SCRIPT_PATH',
           'FILENAME',
           'SHOTNAME')



import os
import sys
import time
import logging
from functools import wraps

import hashlib

import requests as req
from urllib.parse import quote,unquote

import re
import json
import html
import pickle
from bs4 import BeautifulSoup



PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')
SCRIPT_PATH,FILENAME = os.path.split(os.path.realpath(sys.argv[0]))
SCRIPT_PATH = SCRIPT_PATH.replace('\\','/')
SHOTNAME = os.path.splitext(FILENAME)[0]



class _User():
    """
    用户属性，一般包括下列五项

    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    level: 用户等级
    gender: 性别
    """


    __slots__ = ('user_name',
                 'nick_name',
                 'portrait',
                 'level',
                 'gender')


    def __init__(self,**kwargs):
        self.user_name = kwargs.get('user_name',None)
        self.nick_name = kwargs.get('nick_name',None)
        self.portrait = kwargs.get('portrait',None)
        self.level = kwargs.get('level',None)
        self.gender = kwargs.get('gender',None)



class _User_Dict(dict):
    """
    可按id检索用户的字典
    _User_Dict(user_list:list)

    参数:
        user_list: 列表 必须是从app接口获取的用户信息列表！
    """


    def __init__(self,user_list:list):
        for user in user_list:
            if user.get('name_show',None):
                level_str = user.get('level_id',None)
                _user = _User(user_name=user['name'] if user['name'] else None,
                              nick_name=user['name_show'] if user['name_show'] != user['name'] else None,
                              portrait=re.search('[\w.-]+',user['portrait']).group(),
                              level=int(level_str) if level_str else None,
                              gender=int(user['gender']) if user['gender'] else None)
                self[user['id']] = _user



class _Web_Thread():
    """
    主题帖信息

    tid: 帖子编号
    pid: 回复编号
    title: 标题
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    reply_num: 回复数
    """


    __slots__ = ('tid',
                 'pid',
                 'title',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'reply_num')


    def __init__(self):
        pass



class _App_Thread(_Web_Thread):
    """
    主题帖信息

    tid: 帖子编号
    pid: 回复编号
    title: 标题
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    gender: 性别
    reply_num: 回复数
    like: 点赞数
    dislike: 点踩数
    """


    __slots__ = ('tid',
                 'pid',
                 'title',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'gender',
                 'reply_num',
                 'like',
                 'dislike',)


    def __init__(self):
        super(_App_Thread,self).__init__()
        pass


    def _init_userinfo(self,user:_User):
        """
        利用_User实例初始化自身属性
        _init_userinfo(user:_User)
        """

        self.user_name = user.user_name
        self.nick_name = user.nick_name
        self.portrait = user.portrait
        self.gender = user.gender



class _Web_Post():
    """
    楼层信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    level: 用户等级
    floor: 楼层数
    is_thread_owner: 是否楼主
    comment_num: 楼中楼回复数
    sign: 签名图片
    imgs: 图片列表
    smileys: 表情列表
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



class _App_Post(_Web_Post):
    """
    楼层信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    level: 用户等级
    gender: 性别
    floor: 楼层数
    is_thread_owner: 是否楼主
    comment_num: 楼中楼回复数
    like: 点赞数
    dislike: 点踩数
    sign: 小尾巴文本
    imgs: 图片列表
    smileys: 表情列表
    """


    __slots__ = ('text',
                 'tid',
                 'pid',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'level',
                 'gender',
                 'floor',
                 'is_thread_owner',
                 'comment_num',
                 'like',
                 'dislike',
                 'sign',
                 'imgs',
                 'smileys')


    def __init__(self):
        super(_App_Post,self).__init__()
        pass


    def _init_content(self,content_fragments:list):
        """
        从回复内容的碎片列表中提取有用信息
        _init_content(content_fragments:list)
        """

        texts = []
        self.imgs = []
        self.smileys = []
        for fragment in content_fragments:
            if fragment['type'] == '0':
                texts.append(fragment['text'])
            elif fragment['type'] == '2':
                self.smileys.append(fragment['text'])
            elif fragment['type'] == '3':
                self.imgs.append(fragment['origin_src'])
        self.text = ''.join(texts)


    def _init_userinfo(self,user:_User):
        """
        利用_User实例初始化自身属性
        _init_userinfo(user:_User)
        """

        self.user_name = user.user_name
        self.nick_name = user.nick_name
        self.portrait = user.portrait
        self.level = user.level
        self.gender = user.gender



class _Web_Comment():
    """
    楼中楼信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    smileys: 表情列表
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



class _App_Comment(_Web_Comment):
    """
    楼中楼信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    level: 用户等级
    gender: 性别
    like: 点赞数
    dislike: 点踩数
    smileys: 表情列表
    """


    __slots__ = ('text',
                 'tid',
                 'pid',
                 'user_name',
                 'nick_name',
                 'portrait',
                 'level',
                 'gender',
                 'like',
                 'dislike',
                 'smileys')


    def __init__(self):
        super(_App_Comment,self).__init__()
        pass


    def _init_content(self,content_fragments:list):
        """
        从回复内容的碎片列表中提取有用信息
        _init_content(content_fragments:list)
        """

        texts = []
        self.smileys = []
        for fragment in content_fragments:
            if fragment['type'] == '0':
                texts.append(fragment['text'])
            elif fragment['type'] == '2':
                self.smileys.append(fragment['text'])
        self.text = ''.join(texts)


    def _init_userinfo(self,user:_User):
        """
        利用_User实例初始化自身属性
        _init_userinfo(user:_User)
        """

        self.user_name = user.user_name
        self.nick_name = user.nick_name
        self.portrait = user.portrait
        self.level = user.level
        self.gender = user.gender



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

    app_thread_api = 'http://c.tieba.baidu.com/c/f/frs/page'
    app_post_api = 'http://c.tieba.baidu.com/c/f/pb/page'
    app_comment_api = 'http://c.tieba.baidu.com/c/f/pb/floor'
    app_headers = {'Content-Type':'multipart/form-data',
                   'x_bd_data_type':'protobuf',
                   'Charset':'UTF-8',
                   'cuid_galaxy2':'573B24810C196E865FCB86C51EF8AC09|VDVSTWVBW',
                   'User-Agent':'bdtb for Android 11.6.8.2',
                   'Connection':'Keep-Alive',
                   'c3_aid':'A00-J63VLDXPDOTDMRZVGYYOLCWFVKGRXMQO-UVT3YYGX',
                   'Accept-Encoding':'gzip',
                   'cuid':'573B24810C196E865FCB86C51EF8AC09|VDVSTWVBW',
                   'client_type':'2',
                   'Host':'c.tieba.baidu.com',
                   }


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
        return True if re.search('[^\u4e00-\u9fa5\w]',name) else False



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



    @staticmethod
    def _app_sign(data:dict):
        """
        对参数字典做贴吧客户端签名
        """

        if data.__contains__('sign'):
            del data['sign']

        raw_list = []
        for key,value in data.items():
            raw_list.extend([str(key),'=',str(value)])
        raw_str = ''.join(raw_list) + 'tiebaclient!!!'

        md5 = hashlib.md5()
        md5.update(raw_str.encode('utf-8'))
        data['sign'] = md5.hexdigest().upper()

        return data



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



    def _web_get_threads(self,tb_name,pn=0):
        """
        获取首页帖子
        _get_threads(tb_name,pn=0)

        返回值:
            list(_Web_Thread)
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
                thread = _Web_Thread()
                thread.tid = int(re.search('href="/p/(\d*)', raw).group(1))
                thread.pid = re.search('"first_post_id":(.*?),', raw).group(1)
                thread.title = html.unescape(re.search('href="/p/.*?" title="([\s\S]*?)"', raw).group(1))
                thread.reply_num = int(re.search('"reply_num":(.*?),',raw).group(1))
                thread.user_name = re.search('''frs-author-name-wrap"><a rel="noreferrer"  data-field='{"un":"(.*?)",''',raw).group(1).encode('utf-8').decode('unicode_escape')
                thread.nick_name = re.search('title="主题作者: (.*?)"', raw).group(1)
                thread.portrait = re.search('id":"(.*?)"}',raw).group(1)
            except(AttributeError):
                continue
            else:
                threads.append(thread)

        return threads



    def _web_get_posts(self,tid,pn=1):
        """
        获取帖子回复
        _get_post(tid,pn=1)

        返回值:
            has_next: 是否还有下一页
            list(_Web_Post)
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
                post = _Web_Post()
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
                post.smileys = [re.search('/(.+?)\.(png|gif|jp.?g)',i["src"]).group() for i in smileys_raw]

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



    def _web_get_comments(self,tid,pid,pn=1):
        """
        获取楼中楼回复
        _get_comment(tid,pid,pn=1)

        返回值:
            has_next: 是否还有下一页
            list(_Web_Comment)
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
                comment = _Web_Comment()
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



    def _app_get_threads(self,tb_name,pn=1,rn=30):
        """
        使用客户端api获取帖子
        _app_get_threads(self,tb_name,rn=30)

        参数:
            tb_name: 字符串 贴吧名
            rn: 整型 每页帖子数
        返回值:
            list(_App_Thread)
        """

        payload = {'_client_id':'wappc_1595296730520_220',
                   '_client_type':2,
                   '_client_version':'11.6.8.2',
                   '_phone_imei':'869346037118962',
                   'from':'tieba',
                   'kw':tb_name,
                   'pn':pn,
                   'q_type':2,
                   'rn':rn,
                   'with_group':1
                   }

        retry_times = 20
        while retry_times:
            try:
                res = req.post(self.app_thread_api,
                               data=self._app_sign(payload),
                               headers=self.app_headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0.5)

        if not raw:
            self.log.error("Failed to get posts of {tid}".format(tid=tid))
            return False,[]

        main_json = json.loads(raw,strict=False)

        users = _User_Dict(main_json['user_list'])

        threads = []
        for thread_raw in main_json['thread_list']:
            thread = _App_Thread()
            thread.tid = thread_raw['tid']
            thread.pid = thread_raw['first_post_id']

            thread.title = thread_raw['title']
            thread.like = int(thread_raw['agree_num'])
            thread.dislike = int(thread_raw['disagree_num'])

            thread._init_userinfo(users[thread_raw['author_id']])

            thread.reply_num = int(thread_raw['reply_num'])

            threads.append(thread)

        return threads



    def _app_get_posts(self,tid,pn=1,rn=30):
        """
        使用客户端api获取回复
        _app_get_posts(tid,pn=1,rn=30)

        参数:
            tid: 整型 帖子序号
            pn: 整型 页数
            rn: 整型 每页帖子数
        返回值:
            has_next: 是否还有下一页
            list(_App_Post)
        """

        payload = {'_client_id':'wappc_1595296730520_220',
                   '_client_type':2,
                   '_client_version':'11.8.6.2',
                   '_phone_imei':'869346037118962',
                   'from':'tieba',
                   'kz':tid,
                   'pn':pn,
                   'rn':rn
                   }

        raw = None
        retry_times = 20
        while retry_times:
            try:
                res = req.post(self.app_post_api,
                               data=self._app_sign(payload),
                               headers=self.app_headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0.5)

        if not raw:
            self.log.error("Failed to get posts of {tid}".format(tid=tid))
            return False,[]

        main_json = json.loads(raw,strict=False)
        
        thread_owner_id = main_json["thread"]['author']['id']

        users = _User_Dict(main_json['user_list'])

        posts = []
        for post_raw in main_json['post_list']:
            post = _App_Post()
            post.tid = tid
            post.pid = post_raw['id']

            post._init_userinfo(users[post_raw['author_id']])

            post._init_content(post_raw['content'])
            post.like = int(post_raw['agree']['agree_num'])
            post.dislike = int(post_raw['agree']['disagree_num'])

            post.is_thread_owner = True if post_raw['author_id'] == thread_owner_id else False
            post.floor = int(post_raw['floor'])
            post.comment_num = int(post_raw['sub_post_number'])

            sign_text = ''
            if post_raw['signature']:
                post.sign = ''.join([sign['text'] for sign in post_raw['signature']['content'] if sign['type'] == '0'])
            else:
                post.sign = None

            posts.append(post)

        has_next = True if main_json['page']['has_more'] == '1' else False

        return has_next,posts



    def _app_get_comments(self,tid,pid,pn=1):
        """
        使用客户端api获取回复
        _app_get_comments(tid,pid,pn=1)

        参数:
            tid: 整型 帖子序号
            pid: 字符串 回复编号
            pn: 整型 页数
        返回值:
            has_next: 是否还有下一页
            list(_App_Comment)
        """

        payload = {'_client_id':'wappc_1595296730520_220',
                   '_client_type':'2',
                   '_client_version':'11.6.8.2',
                   '_phone_imei':'869346037118962',
                   'from':'tieba',
                   'kz':tid,
                   'pid':pid,
                   'pn':pn
                   }

        retry_times = 20
        while retry_times:
            try:
                res = req.post(self.app_comment_api,
                               data=self._app_sign(payload),
                               headers=self.app_headers)
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

        main_json = json.loads(raw,strict=False)

        comments = []
        for comment_raw in main_json['subpost_list']:
            comment = _App_Comment()
            comment.tid = int(tid)
            comment.pid = comment_raw['id']

            comment._init_content(comment_raw['content'])
            comment.like = int(comment_raw['agree']['agree_num'])
            comment.dislike = int(comment_raw['agree']['disagree_num'])

            author_info = comment_raw['author']
            comment.user_name = author_info['name']
            comment.nick_name = author_info['name_show'] if author_info['name_show'] != author_info['name'] else None
            comment.portrait = re.search('[\w.-]+',author_info['portrait']).group()
            comment.level = int(author_info['level_id'])
            comment.gender = int(author_info['gender'])

            comments.append(comment)

        has_next = True if main_json['page']['current_page'] != main_json['page']['total_page'] else False

        return has_next,comments