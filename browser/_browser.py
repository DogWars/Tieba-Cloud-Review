# -*- coding:utf-8 -*-
__all__ = ('Browser','log',
           'UserInfo',
           'Web_Thread','Web_Post','Web_Comment',
           'Thread','Post','Comment',
           'SHOTNAME')



import os
import sys
import time
import traceback
from functools import wraps

import hashlib

import requests as req

import re
import json
import html
import pickle
from bs4 import BeautifulSoup

from ._logger import log,SHOTNAME



PATH = os.path.split(os.path.realpath(__file__))[0]



class UserInfo(object):
    """
    用户属性，一般包括下列五项

    user_name: 发帖用户名
    nick_name: 发帖人昵称
    portrait: 用户头像portrait值
    gender: 性别（1男2女0未知）
    """


    __slots__ = ('user_name',
                 'nick_name',
                 'portrait',
                 'gender')


    def __init__(self):
        self.user_name = ""
        self.nick_name = ""
        self.portrait = ""
        self.gender = 0



class UserInfo_Dict(dict):
    """
    可按id检索用户的字典
    UserInfo_Dict(user_list:list)

    参数:
        user_list: list 必须是从app接口获取的用户信息列表！
    """


    def __init__(self,user_list:list):
        for user in user_list:
            if not user.__contains__('name_show'):
                continue

            _user = UserInfo()

            try:
                if user.get('level_id',0):
                    level = int(user['level_id'])
                else:
                    level = 0
                _user.user_name = user.get('name','')
                if user['name_show'] != user['name']:
                    _user.nick_name = user['name_show']
                _user.portrait = re.match('[\w.-]+',user['portrait']).group()
                if user.get('gender',0):
                    _user.gender = int(user['gender'])
            except KeyError:
                log.error(traceback.format_exc())

            self[user['id']] = (_user,level)



class BaseContent(object):
    """
    基本的内容信息

    tid: 帖子编号
    pid: 回复编号
    text: 文本内容
    user: UserInfo类 发布者信息
    """


    __slots__ = ('_tid','_pid',
                 'text',
                 'user')


    def __init__(self):
        self._tid = 0
        self._pid = 0
        self.text = ''
        self.user = UserInfo()


    @property
    def tid(self):
        return self._tid

    @tid.setter
    def tid(self,new_tid):
        self._tid = int(new_tid)


    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self,new_pid):
        self._pid = int(new_pid)



class Web_Thread(BaseContent):
    """
    主题帖信息

    text: 标题文本
    tid: 帖子编号
    pid: 回复编号
    reply_num: 回复数
    has_audio: 是否含有音频
    has_video: 是否含有视频
    user: UserInfo类 发布者信息
    """


    __slots__ = ('_reply_num',
                 'has_audio','has_video')


    def __init__(self):
        super(Web_Thread,self).__init__()
        self._reply_num = 0
        self.has_audio = False
        self.has_video = False


    @property
    def reply_num(self):
        return self._reply_num

    @reply_num.setter
    def reply_num(self,new_reply_num):
        self._reply_num = int(new_reply_num)


class Thread(Web_Thread):
    """
    主题帖信息

    text: 标题文本
    tid: 帖子编号
    pid: 回复编号
    first_floor: 首楼内容
    reply_num: 回复数
    has_audio: 是否含有音频
    has_video: 是否含有视频
    like: 点赞数
    dislike: 点踩数
    create_time: 10位时间戳 创建时间
    last_time: 10位时间戳 最后回复时间
    user: UserInfo类 发布者信息
    """


    __slots__ = ('first_floor',
                 '_like','_dislike',
                 '_create_time','_last_time')


    def __init__(self):
        super(Thread,self).__init__()
        self.first_floor = ''
        self._like = 0
        self._dislike = 0
        self._create_time = 0
        self._last_time = 0


    @property
    def like(self):
        return self._like

    @like.setter
    def like(self,new_like):
        self._like = int(new_like)


    @property
    def dislike(self):
        return self._dislike

    @dislike.setter
    def dislike(self,new_dislike):
        self._dislike = int(new_dislike)


    @property
    def create_time(self):
        return self._create_time

    @create_time.setter
    def create_time(self,new_create_time):
        self._create_time = int(new_create_time)


    @property
    def last_time(self):
        return self._last_time

    @last_time.setter
    def last_time(self,new_last_time):
        self._last_time = int(new_last_time)



    def _init_content(self,content_fragments:list):
        """
        从回复内容的碎片列表中提取有用信息
        _init_content(content_fragments:list)
        """

        texts = []
        for fragment in content_fragments:
            if fragment['type'] in ['0','1','4','18']:
                texts.append(fragment['text'])
        self.first_floor = ''.join(texts)



class Web_Post(BaseContent):
    """
    楼层信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    reply_num: 楼中楼回复数
    floor: 楼层数
    has_audio: 是否含有音频
    create_time: 10位时间戳，创建时间
    sign: 签名图片
    imgs: 图片列表
    smileys: 表情列表
    user: UserInfo类 发布者信息
    level: 用户等级
    is_thread_owner: 是否楼主
    """


    __slots__ = ('_reply_num',
                 '_floor',
                 'has_audio',
                 '_create_time',
                 'sign','imgs','smileys',
                 '_level','is_thread_owner')


    def __init__(self):
        super(Web_Post,self).__init__()
        self._reply_num = 0
        self._floor = 0
        self.has_audio = False
        self._create_time = 0
        self.sign = ''
        self.imgs = []
        self.smileys = []
        self._level = 0
        self.is_thread_owner = False


    @property
    def reply_num(self):
        return self._reply_num

    @reply_num.setter
    def reply_num(self,new_reply_num):
        self._reply_num = int(new_reply_num)


    @property
    def floor(self):
        return self._floor

    @floor.setter
    def floor(self,new_floor):
        self._floor = int(new_floor)


    @property
    def create_time(self):
        return self._create_time

    @create_time.setter
    def create_time(self,new_create_time):
        self._create_time = int(new_create_time)


    @property
    def level(self):
        return self._level

    @level.setter
    def level(self,new_level):
        self._level = int(new_level)


class Post(Web_Post):
    """
    楼层信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    reply_num: 楼中楼回复数
    like: 点赞数
    dislike: 点踩数
    floor: 楼层数
    has_audio: 是否含有音频
    create_time: 10位时间戳，创建时间
    sign: 签名图片
    imgs: 图片列表
    smileys: 表情列表
    user: UserInfo类 发布者信息
    level: 用户等级
    is_thread_owner: 是否楼主
    """


    __slots__ = ('_like',
                 '_dislike')


    def __init__(self):
        super(Post,self).__init__()
        self._like = 0
        self._dislike = 0


    @property
    def like(self):
        return self._like

    @like.setter
    def like(self,new_like):
        self._like = int(new_like)


    @property
    def dislike(self):
        return self._dislike

    @dislike.setter
    def dislike(self,new_dislike):
        self._dislike = int(new_dislike)


    def _init_content(self,content_fragments:list):
        """
        从回复内容的碎片列表中提取有用信息
        _init_content(content_fragments:list)
        """

        texts = []
        self.imgs = []
        self.smileys = []
        self.has_audio = False
        for fragment in content_fragments:
            if fragment['type'] in ['0','1','4','18']:
                texts.append(fragment['text'])
            elif fragment['type'] == '2':
                self.smileys.append(fragment['text'])
            elif fragment['type'] == '3':
                self.imgs.append(fragment['origin_src'])
            elif fragment['type'] == '10':
                self.has_audio = True
        self.text = ''.join(texts)


class Web_Comment(BaseContent):
    """
    楼中楼信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    has_audio: 是否含有音频
    create_time: 10位时间戳，创建时间
    smileys: 表情列表
    user: UserInfo类 发布者信息
    """


    __slots__ = ('has_audio',
                 '_create_time',
                 'smileys')


    def __init__(self):
        super(Web_Comment,self).__init__()
        self.has_audio = False
        self._create_time = 0
        self.smileys = []


    @property
    def create_time(self):
        return self._create_time

    @create_time.setter
    def create_time(self,new_create_time):
        self._create_time = int(new_create_time)


class Comment(Web_Comment):
    """
    楼中楼信息

    text: 正文
    tid: 帖子编号
    pid: 回复编号
    like: 点赞数
    dislike: 点踩数
    has_audio: 是否含有音频
    create_time: 10位时间戳，创建时间
    smileys: 表情列表
    user: UserInfo类 发布者信息
    level: 用户等级
    """


    __slots__ = ('_like','_dislike',
                 '_level')


    def __init__(self):
        super(Comment,self).__init__()
        pass


    @property
    def like(self):
        return self._like

    @like.setter
    def like(self,new_like):
        self._like = int(new_like)


    @property
    def dislike(self):
        return self._dislike

    @dislike.setter
    def dislike(self,new_dislike):
        self._dislike = int(new_dislike)


    @property
    def level(self):
        return self._level

    @level.setter
    def level(self,new_level):
        self._level = int(new_level)


    def _init_content(self,content_fragments:list):
        """
        从回复内容的碎片列表中提取有用信息
        _init_content(content_fragments:list)
        """

        texts = []
        self.smileys = []
        self.has_audio = False
        for fragment in content_fragments:
            if fragment['type'] in ['0','1','4']:
                texts.append(fragment['text'])
            elif fragment['type'] == '2':
                self.smileys.append(fragment['text'])
            elif fragment['type'] == '10':
                self.has_audio = True
        self.text = ''.join(texts)



class _Headers(object):
    """
    消息头
    """


    __slots__ = ('headers','cookies','app_headers','app_cookies')


    def __init__(self,filepath):
        self.update(filepath)

        self.app_headers = {'Content-Type':'application/x-www-form-urlencoded',
                           'Charset':'UTF-8',
                           'User-Agent':'bdtb for Android 11.8.8.7',
                           'Connection':'Keep-Alive',
                           'client_logid':'1600505010776',
                           'client_user_token':'957339815',
                           'cuid':'573B24810C196E865FCB86C51EF8AC09|VDVSTWVBW',
                           'cuid_galaxy2':'573B24810C196E865FCB86C51EF8AC09|VDVSTWVBW',
                           'cuid_gid':'',
                           'c3_aid':'A00-J63VLDXPDOTDMRZVGYYOLCWFVKGRXMQO-UVT3YYGX',
                           'client_type':'2',
                           'Accept-Encoding':'gzip',
                           'Host':'c.tieba.baidu.com',
                           }

        self.app_cookies = {'TBBRAND':'TAS-AN00',
                            'BAIDUCUID':'gu2wu_aIB8guivtqg8-Y8_iXHuYduS8Kg8H0fl8Ovf8j9HMJJk1yRhEmA',
                            'CUID':self.app_headers['cuid'],
                            'ka':'open',
                            'BAIDUZID':'000'
                            }


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
                    if re.match('GET|POST',text):
                        continue
                    else:
                        text = text.replace('\n','').split(':',1)
                        self.headers[text[0].strip().capitalize()] = text[1].strip()
        except (FileExistsError):
            log.critical("headers.txt not exist! Please create it from browser!")
            raise(FileExistsError("headers.txt not exist! Please create it from browser!"))

        if self.headers.__contains__('Referer'):
            del self.headers['Referer']
        if self.headers.__contains__('Cookie'):
            for text in self.headers['Cookie'].split(';'):
                text = text.strip().split('=')
                self.cookies[text[0]] = text[1]
        else:
            log.critical("raw_headers[\"cookies\"] not found!")
            raise(AttributeError("raw_headers[\"cookies\"] not found!"))


    def _set_host(self,url):
        try:
            self.headers['Host'] = re.search('://(.+?)/',url).group(1)
        except AttributeError:
            return False
        else:
            return True



class _Basic_API(object):
    """
    贴吧浏览、参数获取等基本api
    """


    __slots__ = ('tieba_url',
                 'tieba_post_url',
                 'comment_url',
                 'user_homepage_url',

                 'tbs_api',
                 'fid_api',
                 'user_json_api',
                 'panel_api',
                 'self_info_api',

                 'app_thread_api',
                 'app_post_api',
                 'app_comment_api')


    def __init__(self):
        self.tieba_url = 'http://tieba.baidu.com/f'
        self.tieba_post_url = 'http://tieba.baidu.com/p/'
        self.comment_url = 'http://tieba.baidu.com/p/comment'
        self.user_homepage_url = 'https://tieba.baidu.com/home/main/'

        self.tbs_api = 'http://tieba.baidu.com/dc/common/tbs'
        self.fid_api = 'http://tieba.baidu.com/sign/info'
        self.user_json_api = 'http://tieba.baidu.com/i/sys/user_json'
        self.panel_api = 'https://tieba.baidu.com/home/get/panel'
        self.self_info_api = 'http://tieba.baidu.com/f/user/json_userinfo'

        self.app_thread_api = 'http://c.tieba.baidu.com/c/f/frs/page'
        self.app_post_api = 'http://c.tieba.baidu.com/c/f/pb/page'
        self.app_comment_api = 'http://c.tieba.baidu.com/c/f/pb/floor'



class Browser(object):
    """
    贴吧浏览、参数获取等API的封装
    Browser(headers_filepath:str)
    """


    __slots__ = ('start_time',
                 'fid_cache_filepath',
                 'fid_dict',
                 'account',
                 'api')


    def __init__(self,headers_filepath:str):
        """
        Browser(headers_filepath:str)
        """

        self.start_time = time.time()

        log_dir = os.path.join(PATH,'log')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        self.fid_cache_filepath = os.path.join(PATH,'cache/fid_cache.pk')
        try:
            with open(self.fid_cache_filepath,'rb') as pickle_file:
                self.fid_dict = pickle.load(pickle_file)
        except IOError:
            log.warning('"{filepath}" not found. Create new fid_dict'.format(filepath=self.fid_cache_filepath))
            self.fid_dict = {}

        self.account = _Headers(headers_filepath)

        self.api = _Basic_API()


    def quit(self):
        """
        自动缓存fid信息
        """

        try:
            with open(self.fid_cache_filepath,'wb') as pickle_file:
                pickle.dump(self.fid_dict,pickle_file)
        except AttributeError:
            log.warning("Failed to save fid cache!")

        log.debug('Time cost:{t:.3f}'.format(t=time.time() - self.start_time))


    @staticmethod
    def timestamp2str(timestamp):
        """
        时间戳转格式化字符串
        timestamp2str(timestamp)

        参数:
            timestamp: int 时间戳

        返回值:
            timestr: str 格式化字符串
        """
        timestamp = int(timestamp)
        time_local = time.localtime(timestamp)
        timestr = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
        return timestr


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


    def _is_vip(self,keyword):
        """
        判断指定用户的vip状态
        _is_vip(keyword)

        参数:
            keyword: str 用户的user_name或portrait

        返回值:
            is_vip: bool 是否vip
        """

        if keyword.startswith('tb.'):
            params = {'id':keyword}
        else:
            params = {'un':keyword}

        self._set_host(self.api.panel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.api.panel_api,
                              params=params,
                              headers=self.account.headers)
            except req.exceptions.RequestException:
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
            log.warning('Failed to get vip status of {keyword}!'.format(keyword=keyword))
            return None


    def _is_self_vip(self):
        """
        当前加载的account是否vip
        _is_self_vip()

        返回值:
            is_vip: bool 当前账号是否vip
        """

        self._set_host(self.api.self_info_api)
        portrait = None
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.api.self_info_api,
                              headers=self.account.headers)
            except req.exceptions.RequestException:
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
            log.error("Failed to get self info")
            return None

        return self._is_vip(portrait)


    def _set_host(self,url):
        """
        设置消息头的host字段
        _set_host(url)

        参数:
            url: str 待请求的地址
        """

        if self.account._set_host(url):
            return True
        else:
            log.warning('Wrong type of url "{url}"!'.format(url=url))
            return False


    def _get_tbs(self):
        """
        获取贴吧反csrf校验码tbs
        _get_tbs()

        返回值:
            tbs: str 反csrf校验码tbs
        """

        self._set_host(self.api.tbs_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.get(self.api.tbs_api,
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"tbs":"([a-z\d]+)',res.text)
                    if raw:
                        tbs = raw.group(1)
                        return tbs
            retry_times-=1
            time.sleep(0.25)

        log.error("Failed to get tbs")
        return ''


    def _tbname2fid(self,tb_name):
        """
        通过贴吧名获取forum_id
        _tbname2fid(tb_name)

        参数:
            tb_name: str 贴吧名

        返回值:
            fid: int 该贴吧的forum_id
        """

        if self.fid_dict.__contains__(tb_name):
            return self.fid_dict[tb_name]
        else:
            self._set_host(self.api.fid_api)
            retry_times = 10
            while retry_times:
                try:
                    res = req.get(self.api.fid_api,
                                  params={'kw':tb_name,'ie':'utf-8'},
                                  headers=self.account.headers)
                except req.exceptions.RequestException:
                    pass
                else:
                    if res.status_code == 200:
                        raw = re.search('"forum_id":(\d+)', res.text)
                        if raw:
                            fid = int(raw.group(1))
                            self.fid_dict[tb_name] = fid
                            return fid
                retry_times-=1
                time.sleep(0.25)

        log.critical("Failed to get fid of {name}".format(name=tb_name))
        raise(ValueError("Failed to get fid of {name}".format(name=tb_name)))


    def _name2portrait(self,name):
        """
        通过用户名或昵称获取portrait
        _name2portrait(name)

        参数:
            name: str user_name或nick_name

        返回值:
            portrait: str 该用户的portrait
        """

        name = str(name)
        self._set_host(self.api.panel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.api.panel_api,
                              params={'un':name},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"portrait":"([\w.-]+)', res.text)
                    if raw:
                        portrait = raw.group(1)
                        return portrait
            retry_times-=1
            time.sleep(0)

        log.error("Failed to get portrait of {name}".format(name=name))
        return ''


    def _name2userid(self,name):
        """
        通过用户名或昵称获取user_id
        _name2userid(name)

        参数:
            name: str user_name或nick_name

        返回值:
            user_id: int 该用户的user_id
        """

        self._set_host(self.api.panel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.api.panel_api,
                              params={'un':name},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('"id":(\d+)', res.text)
                    if raw:
                        user_id = int(raw.group(1))
                        return user_id
            retry_times-=1
            time.sleep(0)

        log.error("Failed to get user_id of {name}".format(name=name))
        return 0


    def _portrait2names(self,portrait):
        """
        用portrait获取user_name和nick_name
        _portrait2names(portrait)

        参数:
            portrait: str 用户的portrait

        返回值:
            (user_name,nick_name)
        """

        if not portrait.startswith('tb.'):
            log.error("Wrong portrait format {portrait}".format(portrait=portrait))
            return ('','')

        self._set_host(self.api.panel_api)
        raw = None
        retry_times = 3
        while retry_times:
            try:
                res = req.get(self.api.panel_api,
                              params={'id':portrait},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = json.loads(res.text)
                    if raw['error'] == '成功':
                        break
            retry_times-=1
            time.sleep(0)

        if not raw or not raw['error'] == '成功':
            log.error("Failed to get user_id of {name}".format(name=name))
            return ('','')

        user_name = raw['data']['name']
        nick_name = raw['data']['name_show']
        return (user_name,nick_name)


    def _web_get_threads(self,tb_name,pn=0):
        """
        使用网页版api获取首页帖子
        _web_get_threads(tb_name,pn=0)

        参数:
            tb_name: str 贴吧名
            pn: int 页码（每页50帖）

        返回值:
            threads: list(Web_Thread)
        """

        threads = []
        self._set_host(self.api.tieba_url)
        raws = []
        retry_times = 25
        while retry_times:
            try:
                res = req.get(self.api.tieba_url,
                              params={'kw':tb_name,'pn':pn * 50,'ie':'utf-8'},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raws = re.findall('thread_list clearfix([\s\S]*?)创建时间"',html.unescape(res.text))
                    if raws:
                        break
            retry_times-=1
            time.sleep(0)

        if not raws:
            log.error("Failed to get threads in {tb_name}!".format(tb_name=tb_name))
            return threads

        for raw in raws:
            try:
                thread = Web_Thread()
                thread.tid = re.search('href="/p/(\d*)', raw).group(1)
                thread.pid = re.search('"first_post_id":(.*?),', raw).group(1)
                thread.text = html.unescape(re.search('href="/p/.*?" title="([\s\S]*?)"', raw).group(1))
                thread.reply_num = re.search('"reply_num":(.*?),',raw).group(1)

                if re.search('data-thread-type="11"',raw):
                    thread.has_audio = True
                if re.search('data-thread-type="40"',raw):
                    thread.has_video = True

                thread.user.user_name = re.search('''frs-author-name-wrap"><a rel="noreferrer"  data-field='{"un":"(.*?)",''',raw).group(1).encode('utf-8').decode('unicode_escape')
                thread.user.nick_name = re.search('title="主题作者: (.*?)"', raw).group(1)
                thread.user.portrait = re.search('id":"(.*?)"}',raw).group(1)

            except AttributeError:
                continue
            else:
                threads.append(thread)

        return threads


    def _web_get_posts(self,tid,pn=1):
        """
        使用网页版api获取主题帖内回复
        _web_get_posts(tid,pn=1)

        参数:
            tid: int 主题帖tid
            pn: int 页码

        返回值:
            has_next: bool 是否还有下一页
            posts: list(Web_Post)
        """

        self._set_host(self.api.tieba_post_url)

        raw = None
        retry_times = 25
        while retry_times:
            try:
                res = req.get(self.api.tieba_post_url + str(tid),
                              params={'pn':pn},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('<div class="p_postlist" id="j_p_postlist">.*</div>',res.text,re.S)
                    if raw:
                        raw = raw.group()
                        break
            retry_times-=1
            time.sleep(0)

        if not raw:
            log.error("Failed to get posts of {tid}".format(tid=tid))
            return False,[]

        has_next = True if re.search('<a href=".*">尾页</a>',raw) else False
        content = BeautifulSoup(raw,'lxml')
        post_list = []
        try:
            posts = content.find_all("div",{'data-field':True,'data-pid':True})
            for post_raw in posts:
                post = Web_Post()
                post.tid = tid

                text_raw = post_raw.find("div",id=re.compile('^post_content_\d+$'))
                post.text = ''.join(text_raw.strings).strip()

                user_sign = post_raw.find(class_='j_user_sign')
                if user_sign:
                    post.sign = user_sign["src"]

                imgs_raw = text_raw.find_all("img",class_='BDE_Image')
                post.imgs = [i["src"] for i in imgs_raw]

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                post.smileys = [re.search('/(.+?)\.(png|gif|jp.?g)',i["src"]).group() for i in smileys_raw]

                if post_raw.find("div",class_=re.compile('^louzhubiaoshi')):
                    post.is_thread_owner = True
                if post_raw.find("div",class_=re.compile('^voice_player')):
                    post.has_audio = True

                time_raw = post_raw.find("span",class_='tail-info',text=re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}'))
                time_array = time.strptime(time_raw.string, "%Y-%m-%d %H:%M")
                post.create_time = time.mktime(time_array)

                author_info = json.loads(post_raw["data-field"])
                post.pid = author_info["content"]["post_id"]
                post.reply_num = author_info["content"]["comment_num"]
                post.floor = author_info["content"]["post_no"]

                post.user.user_name = author_info["author"]["user_name"]
                post.user.nick_name = author_info["author"]["user_nickname"]
                post.user.portrait = re.search('[^?]*',author_info["author"]["portrait"]).group()
                post.level = post_raw.find('div',attrs={'class':'d_badge_lv'}).text

                post_list.append(post)

        except KeyError:
            log.error("KeyError: Failed to get posts of {tid}".format(tid=tid))
            return False,[]
        else:
            return has_next,post_list


    def _web_get_comments(self,tid,pid,pn=1):
        """
        使用网页版api获取楼中楼回复
        _web_get_comments(tid,pid,pn=1)

        参数:
            tid: int 主题帖tid
            pid: int 回复pid
            pn: int 页码

        返回值:
            has_next: bool 是否还有下一页
            comments: list(Web_Comment)
        """   

        self._set_host(self.api.comment_url)
        retry_times = 25
        while retry_times:
            try:
                res = req.get(self.api.comment_url,
                              params={'tid':tid,'pid':pid,'pn':pn},
                              headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0)

        if not raw:
            log.error("Failed to get comments of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return False,[]

        content = BeautifulSoup(res.text,'lxml')
        comments = []
        try:
            raws = content.find_all('li',class_=re.compile('^lzl_single_post'))
            has_next = True if content.find('a',string='下一页') else False

            for comment_raw in raws:
                comment = Web_Comment()
                comment_data = json.loads(comment_raw['data-field'])
                comment.tid = tid
                comment.pid = comment_data['spid']
                comment.user.portrait = comment_data['portrait']
                comment.user.user_name = comment_data['user_name']
                nick_name = comment_raw.find('a',class_='at j_user_card').text
                if nick_name != comment.user.user_name:
                    comment.user.nick_name = nick_name

                text_raw = comment_raw.find('span',class_='lzl_content_main')
                comment.text = text_raw.text.strip()

                if comment_raw.find("div",class_=re.compile('^voice_player')):
                    comment.has_audio = True

                time_raw = comment_raw.find('span',class_='lzl_time')
                time_array = time.strptime(time_raw.string, "%Y-%m-%d %H:%M")
                comment.create_time = time.mktime(time_array)

                smileys_raw = text_raw.find_all('img',class_='BDE_Smiley')
                comment.smileys = [i["src"] for i in smileys_raw]

                comments.append(comment)

            return has_next,comments

        except KeyError:
            log.error("KeyError: Failed to get posts of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return False,[]


    def get_threads(self,tb_name,pn=1,rn=30):
        """
        使用客户端api获取首页帖子
        get_threads(tb_name,pn=1,rn=30)

        参数:
            tb_name: str 贴吧名
            pn: int 页码
            rn: int 每页帖子数

        返回值:
            threads: list(Thread)
        """

        payload = {'_client_id':'wappc_1600500414046_633',
                   '_client_type':2,
                   '_client_version':'11.8.8.7',
                   '_phone_imei':'000000000000000',
                   'from':'tieba',
                   'kw':tb_name,
                   'pn':pn,
                   'q_type':2,
                   'rn':rn,
                   'with_group':1
                   }

        retry_times = 25
        while retry_times:
            try:
                res = req.post(self.api.app_thread_api,
                               data=self._app_sign(payload),
                               headers=self.account.app_headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0)

        try:
            main_json = json.loads(raw,strict=False)
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except (json.JSONDecodeError,ValueError):
            log.error("Failed to get threads of {tb_name}".format(tb_name=tb_name))
            return []

        users = UserInfo_Dict(main_json['user_list'])

        threads = []
        for thread_raw in main_json['thread_list']:
            thread = Thread()
            try:
                thread.user = users[thread_raw['author_id']][0]
            except KeyError:
                continue

            thread.tid = thread_raw['tid']
            thread.pid = thread_raw['first_post_id']

            thread.text = thread_raw['title']
            thread._init_content(thread_raw.get('first_post_content',[]))

            if thread_raw.get('voice_info',None):
                thread.has_audio = True
            if thread_raw.get('video_info',None):
                thread.has_video = True

            thread.like = thread_raw['agree_num']
            thread.dislike = thread_raw['disagree_num']

            thread.reply_num = thread_raw['reply_num']
            thread.create_time = thread_raw['create_time']
            thread.last_time = thread_raw['last_time_int']

            threads.append(thread)

        return threads


    def get_posts(self,tid,pn=1,rn=30):
        """
        使用客户端api获取主题帖内回复
        get_posts(tid,pn=1,rn=30)

        参数:
            tid: int 主题帖tid
            pn: int 页码
            rn: int 每页帖子数

        返回值:
            has_next: bool 是否还有下一页
            posts: list(Post)
        """

        payload = {'_client_id':'wappc_1600500414046_633',
                   '_client_type':2,
                   '_client_version':'11.8.8.7',
                   '_phone_imei':'000000000000000',
                   'from':'tieba',
                   'kz':tid,
                   'pn':pn,
                   'rn':rn
                   }

        raw = None
        retry_times = 25
        while retry_times:
            try:
                res = req.post(self.api.app_post_api,
                               data=self._app_sign(payload),
                               headers=self.account.app_headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0)

        try:
            main_json = json.loads(raw,strict=False)
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except (json.JSONDecodeError,ValueError):
            log.error("Failed to get posts of {tid}".format(tid=tid))
            return False,[]

        thread_owner_id = main_json["thread"]['author']['id']

        users = UserInfo_Dict(main_json['user_list'])

        posts = []
        for post_raw in main_json['post_list']:
            post = Post()

            try:
                post.user,post.level = users[post_raw['author_id']]
            except KeyError:
                continue

            post.tid = tid
            post.pid = post_raw['id']

            post._init_content(post_raw['content'])
            post.like = post_raw['agree']['agree_num']
            post.dislike = post_raw['agree']['disagree_num']

            if post_raw['author_id'] == thread_owner_id:
                post.is_thread_owner = True

            post.floor = post_raw['floor']
            post.reply_num = post_raw['sub_post_number']
            post.create_time = post_raw['time']

            if post_raw['signature']:
                post.sign = ''.join([sign['text'] for sign in post_raw['signature']['content'] if sign['type'] == '0'])

            posts.append(post)

        has_next = True if main_json['page']['has_more'] == '1' else False

        return has_next,posts


    def get_comments(self,tid,pid,pn=1):
        """
        使用客户端api获取楼中楼回复
        get_comments(tid,pid,pn=1)

        参数:
            tid: int 主题帖tid
            pid: int 回复pid
            pn: int 页码

        返回值:
            has_next: bool 是否还有下一页
            comments: list(Comment)
        """

        payload = {'_client_id':'wappc_1600500414046_633',
                   '_client_type':'2',
                   '_client_version':'11.8.8.7',
                   '_phone_imei':'000000000000000',
                   'from':'tieba',
                   'kz':tid,
                   'pid':pid,
                   'pn':pn
                   }

        retry_times = 25
        while retry_times:
            try:
                res = req.post(self.api.app_comment_api,
                               data=self._app_sign(payload),
                               headers=self.account.app_headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0)

        if not raw:
            return False,[]

        main_json = json.loads(raw,strict=False)

        try:
            main_json = json.loads(raw,strict=False)
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except (json.JSONDecodeError,ValueError):
            log.error("Failed to get comments of {pid} in thread {tid}".format(tid=tid,pid=pid))
            return False,[]

        comments = []
        for comment_raw in main_json['subpost_list']:
            comment = Comment()
            comment.tid = tid
            comment.pid = comment_raw['id']

            comment._init_content(comment_raw['content'])
            comment.like = comment_raw['agree']['agree_num']
            comment.dislike = comment_raw['agree']['disagree_num']

            author_info = comment_raw['author']
            comment.user.user_name = author_info['name']
            comment.user.nick_name = author_info['name_show'] if author_info['name_show'] != author_info['name'] else None
            comment.user.portrait = re.match('[\w.-]+',author_info['portrait']).group()
            if author_info['gender']:
                comment.user.gender = author_info['gender']
            comment.level = int(author_info['level_id'])

            comment.create_time = int(comment_raw['time'])

            comments.append(comment)

        has_next = True if main_json['page']['current_page'] != main_json['page']['total_page'] else False

        return has_next,comments