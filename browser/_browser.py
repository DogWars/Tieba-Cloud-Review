# -*- coding:utf-8 -*-
__all__ = ('Browser',)



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

from .__define__ import *
from ._logger import log



class _Headers(object):
    """
    消息头

    参数:
        BDUSS_key: str 作为键值从user_control/BDUSS.json中取出BDUSS
    """


    __slots__ = ('headers','BDUSS')


    app_headers = {'Content-Type':'application/x-www-form-urlencoded',
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

    BDUSS_json = None


    def __init__(self,BDUSS_key):

        self.headers = {'Host':'tieba.baidu.com',
                        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.7,en;q=0.5,zh-TW;q=0.3,zh-HK;q=0.2',
                        'Accept-Encoding':'gzip, deflate, br',
                        'DNT':'1',
                        'Cache-Control':'no-cache',
                        'Connection':'keep-alive',
                        'Cookie':None,
                        'Upgrade-Insecure-Requests':'1'
                        }

        self.renew_BDUSS(self.BDUSS_json[BDUSS_key])


    def renew_BDUSS(self,BDUSS):
        """
        更新BDUSS

        参数:
            BDUSS:str
        """

        self.BDUSS = BDUSS
        self.headers['Cookie'] = 'BDUSS={};'.format(BDUSS)


    def _set_host(self,url):
        try:
            self.headers['Host'] = re.search('://(.+?)/',url).group(1)
        except AttributeError:
            return False
        else:
            return True

try:
    file = open(os.path.join(SCRIPT_PATH,'user_control/BDUSS.json'),'r',encoding='utf-8')
    _Headers.BDUSS_json = json.load(file)
    file.close()
except IOError:
    log.critical("Unable to read mysql.json!")
    raise



class _Basic_API(object):
    """
    贴吧浏览、参数获取等基本api
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
    self_at_api = 'http://c.tieba.baidu.com/c/u/feed/atme'

    app_thread_api = 'http://c.tieba.baidu.com/c/f/frs/page'
    app_post_api = 'http://c.tieba.baidu.com/c/f/pb/page'
    app_comment_api = 'http://c.tieba.baidu.com/c/f/pb/floor'



class Browser(object):
    """
    贴吧浏览、参数获取等API的封装
    Browser(BDUSS_key)

    参数:
        BDUSS_key: str 作为键值从user_control/BDUSS.json中取出BDUSS
    """


    __slots__ = ('start_time',
                 'fid_cache_filepath',
                 'fid_dict',
                 'account',
                 'api')


    def __init__(self,BDUSS_key):

        self.start_time = time.time()

        log_dir = os.path.join(SCRIPT_PATH,'log')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        self.fid_cache_filepath = os.path.join(MODULE_PATH,'cache/fid_cache.pk')
        try:
            with open(self.fid_cache_filepath,'rb') as pickle_file:
                self.fid_dict = pickle.load(pickle_file)
        except IOError:
            log.warning('Failed to read fid_cache in "{filepath}". Create a new one.'.format(filepath=self.fid_cache_filepath))
            self.fid_dict = {}

        self.account = _Headers(BDUSS_key)

        self.api = _Basic_API()


    def quit(self):
        """
        自动缓存fid信息
        """

        try:
            with open(self.fid_cache_filepath,'wb') as pickle_file:
                pickle.dump(self.fid_dict,pickle_file)
        except AttributeError:
            log.error("Failed to save fid cache!")

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

        if res.status_code != 200:
            log.error("Failed to get vip status of {keyword}!".format(keyword=keyword))
            return None

        if re.search('"vipInfo":\[\]',res.text):
            return False
        else:
            return True


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
        tbs = ''
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
                        break
            retry_times-=1
            time.sleep(0.25)

        if not tbs:
            log.warning("Failed to get tbs")

        return tbs


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
                            break
                retry_times-=1
                time.sleep(0.25)

        if not fid:
            error_msg = "Failed to get fid of {name}".format(name=tb_name)
            log.critical(error_msg)
            raise(ValueError(error_msg))

        self.fid_dict[tb_name] = fid
        return fid


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
        portrait = ''
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
                        break
            retry_times-=1
            time.sleep(0)

        if not portrait:
            log.warning("Failed to get portrait of {name}".format(name=name))

        return portrait


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
        user_id = 0
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
                        break
            retry_times-=1
            time.sleep(0)

        if not user_id:
            log.warning("Failed to get user_id of {name}".format(name=name))

        return user_id


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
            log.warning("Wrong portrait format {portrait}".format(portrait=portrait))
            return '',''

        self._set_host(self.api.panel_api)
        error_no = 1
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
                    raw_json = res.json()
                    error_no = raw_json['no']
                    break
            retry_times-=1
            time.sleep(0.25)

        if error_no:
            log.warning("Failed to get names of {portrait}".format(portrait=portrait))
            return '',''

        user_name = raw_json['data']['name']
        nick_name = raw_json['data']['name_show']
        if nick_name==user_name:
            nick_name=''

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

        self._set_host(self.api.tieba_url)

        threads = []
        raw = None
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
                    raw = res.text
                    if raw:
                        break
            retry_times-=1
            time.sleep(0)

        if not raw:
            log.error("Failed to get threads in {tb_name}!".format(tb_name=tb_name))
            return threads

        raws = re.findall('thread_list clearfix([\s\S]*?)创建时间"',html.unescape(raw))
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

        posts = Posts()
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
            return posts

        content = BeautifulSoup(raw,'lxml')
        try:
            raws = content.find_all("div",{'data-field':True,'data-pid':True})

            pageinfo_raw = content.find('ul',class_="l_posts_num")
            posts.total_pn = pageinfo_raw.find('span',class_="red",style=False).text
            currpn_raw = pageinfo_raw.find('span',class_="tP")
            if currpn_raw:
                posts.current_pn = currpn_raw.text

            for post_raw in raws:
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

                posts.append(post)

        except KeyError:
            log.error("KeyError - Failed to get posts of {tid}".format(tid=tid))

        return posts


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

        comments = Comments()
        raw = None
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
            log.error("Failed to get comments of {pid} in {tid}".format(tid=tid,pid=pid))
            return comments

        content = BeautifulSoup(raw,'lxml')
        try:
            raws = content.find_all('li',class_=re.compile('^lzl_single_post'))

            pageinfo_raw = content.find('li',class_=re.compile('^lzl_li_pager'))
            comments.total_pn = json.loads(pageinfo_raw['data-field'])['total_page']
            currpn_raw = pageinfo_raw.find('span')
            if currpn_raw:
                comments.current_pn = currpn_raw.text

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

        except KeyError:
            log.error("KeyError - Failed to get posts of {pid} in {tid}".format(tid=tid,pid=pid))

        return comments


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

        res = None
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
                    main_json = res.json()
                    break
            retry_times-=1
            time.sleep(0)

        try:
            if res.status_code != 200:
                raise(ValueError('status code is not 200'))
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except ValueError:
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

        posts = Posts()
        res = None
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
                    main_json = res.json()
                    break
            retry_times-=1
            time.sleep(0)

        try:
            if res.status_code != 200:
                raise(ValueError('status code is not 200'))
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except ValueError:
            log.error("Failed to get posts of {tid}".format(tid=tid))
            return posts

        thread_owner_id = main_json["thread"]['author']['id']

        users = UserInfo_Dict(main_json['user_list'])

        posts._init_pageinfo(main_json['page'])

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

        return posts


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

        comments = Comments()
        res = None
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
                    main_json = res.json()
                    break
            retry_times-=1
            time.sleep(0)

        try:
            if res.status_code != 200:
                raise(ValueError('status code is not 200'))
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except ValueError:
            log.error("Failed to get comments of {pid} in {tid}".format(tid=tid,pid=pid))
            return comments

        comments._init_pageinfo(main_json['page'])

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
            comment.level = author_info['level_id']

            comment.create_time = comment_raw['time']

            comments.append(comment)

        return comments


    def get_self_ats(self):
        """
        获取@信息

        get_self_at()
        """

        payload = {'BDUSS':self.account.BDUSS,
                   '_client_id':'wappc_1600500414046_633',
                   '_client_type':'2',
                   '_client_version':'11.8.8.7',
                   '_phone_imei':'000000000000000'
                   }

        ats = []
        res = None
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.self_at_api,
                               data=self._app_sign(payload),
                               headers=self.account.app_headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    main_json = res.json()
                    break
            retry_times-=1
            time.sleep(0.25)

        try:
            if res.status_code != 200:
                raise(ValueError('status code is not 200'))
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0'))
        except ValueError:
            log.error("Failed to get ats")
            return ats

        for at_raw in main_json['at_list']:
            at = At()
            at.tb_name = at_raw['fname']
            at.tid = at_raw['thread_id']
            at.pid = at_raw['post_id']
            at.text = at_raw['content'].lstrip()

            at.user = UserInfo(at_raw['quote_user'])

            at.create_time = at_raw['time']

            ats.append(at)

        return ats