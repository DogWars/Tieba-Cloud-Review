# -*- coding:utf-8 -*-
__all__ = ('log','SHOTNAME',
           'UserInfo','UserInfo_Dict',
           'Web_Thread','Web_Post','Web_Comment',
           'Thread','Post','Comment',
           'Posts','Comments')



import traceback

import re

from ._logger import log,SHOTNAME



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



class _BaseContent(object):
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



class Web_Thread(_BaseContent):
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



class Web_Post(_BaseContent):
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


class Posts(list):
    """
    post列表

    current_pn: 当前页数
    total_pn: 总页数
    """


    __slots__ = ('_current_pn','_total_pn')


    def __init__(self):
        self.current_pn = 0
        self.total_pn = 0


    @property
    def current_pn(self):
        return self._current_pn

    @current_pn.setter
    def current_pn(self,new_current_pn):
        self._current_pn = int(new_current_pn)


    @property
    def total_pn(self):
        return self._total_pn

    @total_pn.setter
    def total_pn(self,new_total_pn):
        self._total_pn = int(new_total_pn)


    def _init_pageinfo(self,page_info):
        try:
            self.current_pn = page_info['current_page']
            self.total_pn = page_info['total_page']
        except (KeyError,ValueError):
            log.warning(traceback.format_exc())


    @property
    def has_next(self):
        return False if self._current_pn == self._total_pn else True



class Web_Comment(_BaseContent):
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



class Comments(list):
    """
    comment列表

    current_pn: 当前页数
    total_pn: 总页数
    """


    __slots__ = ('_current_pn','_total_pn')


    def __init__(self):
        self.current_pn = 0
        self.total_pn = 0


    @property
    def current_pn(self):
        return self._current_pn

    @current_pn.setter
    def current_pn(self,new_current_pn):
        self._current_pn = int(new_current_pn)


    @property
    def total_pn(self):
        return self._total_pn

    @total_pn.setter
    def total_pn(self,new_total_pn):
        self._total_pn = int(new_total_pn)


    def _init_pageinfo(self,page_info):
        try:
            self.current_pn = page_info['current_page']
            self.total_pn = page_info['total_page']
        except (KeyError,ValueError):
            log.warning(traceback.format_exc())


    @property
    def has_next(self):
        return False if self._current_pn == self._total_pn else True