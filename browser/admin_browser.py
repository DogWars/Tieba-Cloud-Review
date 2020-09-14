# -*- coding:utf-8 -*-
__all__ = ('AdminBrowser',)



import time

import re
import json
import pickle
from bs4 import BeautifulSoup

import requests as req

from ._browser import Browser,_Basic_API,log



class _Admin_API(_Basic_API):
    """
    贴吧管理员功能相关api
    """


    __slots__ = ('old_del_api',
                 'del_post_api',
                 'del_thread_api',
                 'del_threads_api',
                 'old_block_api',
                 'new_block_api',

                 'recover_api',
                 'unblock_api',
                 'good_add_api',
                 'good_cancel_api',
                 'blacklist_add_api',
                 'blacklist_get_api',
                 'blacklist_cancel_api',
                 'top_add_api',
                 'top_vipadd_api',
                 'top_cancel_api',
                 'top_vipcancel_api',
                 'admin_add_api',
                 'admin_del_api',
                 'appeal_list_api',
                 'appeal_handle_api')


    def __init__(self):
        super(_Admin_API,self).__init__()

        self.old_del_api = 'http://tieba.baidu.com/bawu2/postaudit/audit'
        self.del_post_api = 'http://tieba.baidu.com/f/commit/post/delete'
        self.del_thread_api = 'https://tieba.baidu.com/f/commit/thread/delete'
        self.del_threads_api = 'https://tieba.baidu.com/f/commit/thread/batchDelete'
        self.old_block_api = 'http://c.tieba.baidu.com/c/c/bawu/commitprison'
        self.new_block_api = 'http://tieba.baidu.com/pmc/blockid'

        self.recover_api = 'http://tieba.baidu.com/bawu2/platform/resPost'
        self.unblock_api = 'http://tieba.baidu.com/bawu2/platform/cancelFilter'
        self.good_add_api = 'https://tieba.baidu.com/f/commit/thread/good/add'
        self.good_cancel_api = 'https://tieba.baidu.com/f/commit/thread/good/cancel'
        self.blacklist_add_api = 'http://tieba.baidu.com/bawu2/platform/addBlack'
        self.blacklist_get_api = 'http://tieba.baidu.com/bawu2/platform/listBlackUser'
        self.blacklist_cancel_api = 'http://tieba.baidu.com/bawu2/platform/cancelBlack'
        self.top_add_api = 'https://tieba.baidu.com/f/commit/thread/top/add'
        self.top_vipadd_api = 'https://tieba.baidu.com/f/commit/thread/top/madd'
        self.top_cancel_api = 'https://tieba.baidu.com/f/commit/thread/top/cancel'
        self.top_vipcancel_api = 'https://tieba.baidu.com/f/commit/thread/top/mcancel'
        self.admin_add_api = 'http://tieba.baidu.com/bawu2/platform/addBawuMember'
        self.admin_del_api = 'http://tieba.baidu.com/bawu2/platform/delBawuMember'
        self.appeal_list_api = 'http://tieba.baidu.com/bawu2/appeal/list'
        self.appeal_handle_api = 'http://tieba.baidu.com/bawu2/appeal/commit'



class AdminBrowser(Browser):
    """
    提供百度贴吧管理员相关功能
    AdminBrowser(self,headers_filepath:str,admin_type:int)

    参数:
        headers_filepath: 字符串 消息头文件路径
        admin_type: 整型 吧务权限最高允许的封禁天数
    """


    __slots__ = ('admin_type',)

    def __init__(self,headers_filepath:str,admin_type:int):
        super(AdminBrowser,self).__init__(headers_filepath)
        try:
            self.admin_type = admin_type if admin_type in [1,10] else 1
        except AttributeError:
            raise(AttributeError('Incorrect format!'))

        self.api = _Admin_API()


    def quit(self):
        super(AdminBrowser,self).quit()


    def _old_block(self,user,tb_name,day,reason = 'default'):
        """
        使用旧版api的封禁，适用于权限不足的情况，且被封禁用户必须有用户名
        """

        try:
            payload = {'BDUSS':self.account.cookies['BDUSS'],
                       'day':day,
                       'fid':self._tbname2fid(tb_name),
                       'ntn':'banid',
                       'reason':'null',
                       'tbs':self._get_tbs(),
                       'un':user.user_name,
                       'word':tb_name,
                       'z':'4623534287'
                       }
        except KeyError:
            log.error('Failed to block in {tb_name}'.format(tb_name=tb_name))
            return False,user

        payload = self._app_sign(payload)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.old_block_api,
                               data=payload)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"error_code":"0"',res.content.decode('unicode_escape')):
                    log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=user.user_name,tb_name=tb_name,day=day))
                    return True,user
            retry_times-=1

        log.error('Failed to block {name} in {tb_name}'.format(name=user.user_name,tb_name=tb_name))
        return False,user


    def _new_block(self,user,tb_name,day,reason = 'default'):
        """
        使用新版api的封禁，适用于权限充足或需要封禁无用户名用户（仅有带emoji昵称）的情况
        """

        payload = {"ie":"gbk"}
        payload['reason'] = reason
        regenerate_dict = {}

        try:
            payload['day'] = day if day < self.admin_type else self.admin_type
            payload['fid'] = self._tbname2fid(tb_name)
            payload['tbs'] = self._get_tbs()
        except KeyError:
            log.error('AttributeError: Failed to block!')

        if user.user_name:
            name = user.user_name
            regenerate_dict['user_name'] = name
            payload['user_name[]'] = name

        elif user.portrait:
            regenerate_dict['portrait'] = user.portrait
            user_name,nick_name = self._portrait2names(user.portrait)
            if user_name:
                name = user_name
                payload['user_name[]'] = user_name
                user.user_name = user_name
            elif nick_name:
                name = nick_name
                payload['nick_name[]'] = nick_name
                user.nick_name = nick_name
                payload['portrait[]'] = user.portrait
            else:
                log.error('Failed to block {portrait} in {tb_name}'.format(portrait=user.portrait,tb_name=tb_name))
                regenerate_dict['reason'] = 'ERROR'
                return False,user

        elif user.nick_name:
            name = user.nick_name
            portrait = self._name2portrait(name)
            if not portrait:
                log.error('Failed to block {name} in {tb_name}'.format(name=name,tb_name=tb_name))
                regenerate_dict['reason'] = 'ERROR'
                return False,user
            payload['nick_name[]'] = name
            payload['portrait[]'] = portrait
            user.portrait = portrait

        else:
            log.error('Failed to block in {tb_name}'.format(tb_name=tb_name))
            regenerate_dict['reason'] = 'ERROR'
            return False,user

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.new_block_api,
                               data=payload,
                               headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"errno":0',res.content.decode('unicode_escape')):
                    log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=name,tb_name=tb_name,day=payload['day']))
                    return True,user
            retry_times-=1

        log.error('Failed to block {name} in {tb_name}'.format(name=name,tb_name=tb_name))
        regenerate_dict['reason'] = 'ERROR'
        return False,user


    def block(self,user,tb_name,day,reason = '极光 - 贴吧反广告墙'):
        """
        根据需求自动选择api进行封禁，以新版api为优先选择
        block(self,block)

        参数:
            user: UserInfo类 发布者信息
            tb_name: 字符串 吧名
            day: 整型 封禁天数
            reason: 字符串 封禁理由（可选）
        """

        day = int(day)
        if day > self.admin_type and user.user_name:
            return self._old_block(user,tb_name,day,reason)
        else:
            return self._new_block(user,tb_name,day,reason)


    def _del_thread(self,tb_name,tid):
        """
        新api，删主题帖
        _del_thread(tb_name,tid)
        """
        payload = {'commit_from':'pb',
                   'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid
                   }
        self._set_host(self.api.del_thread_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.del_thread_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _del_threads(self,tb_name,tids):
        """
        批量删除主题帖
        _del_threads(tb_name,tids)
        """
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':'_'.join([str(tid) for tid in tids]),
                   'isBan':0
                   }
        self._set_host(self.api.del_threads_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.del_threads_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Success delete thread {tids} in {tb_name}".format(tids=tids,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to delete thread {tids} in {tb_name}".format(tids=tids,tb_name=tb_name))
        return False


    def _del_post(self,tb_name,tid,pid):
        """
        新api，删回复
        _del_post(tb_name,tid,pid)
        """
        payload = {'commit_from':'pb',
                   'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid,
                   'is_vipdel':0,
                   'pid':pid,
                   'is_finf':'false'
                   }
        self._set_host(self.api.del_post_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.del_post_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
        return False


    def _blacklist_add(self,tb_name,name):
        """
        添加用户至黑名单
        _blacklist_add(tb_name,name)

        参数:
            name: 字符串 用户名或昵称
        """
        if not (tb_name or name):
            return False

        name = str(name)
        payload = {'ie':'utf-8',
                   'word':tb_name,
                   'tbs':self._get_tbs(),
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.api.blacklist_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.blacklist_add_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Add {name} to black list in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to add {name} to black list in {tb_name}".format(name=name,tb_name=tb_name))
        return False


    def _blacklist_get(self,tb_name,pn = 1):
        """
        获取吧申诉列表
        _blacklist_get(tb_name,pn=1)

        参数:
            tb_name: 字符串 贴吧名
            pn: 整型 页数
        """
        params = {'word':tb_name,
                  'pn':pn
                  }
        self._set_host(self.api.blacklist_get_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.get(self.api.blacklist_get_api,
                              params = params,
                              headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = re.search('<tbody>.*</tbody>',res.text,re.S)
                    if raw:
                        raw = raw.group()
                        break
            retry_times-=1
            time.sleep(0.5)

        if not raw:
            log.error("Failed to get black_list of {tb_name}".format(tb_name=tb_name))
            return False,[]

        has_next = True if re.search('class="next_page"',res.text) else False
        content = BeautifulSoup(raw,'lxml')
        black_list = []
        try:
            blacks = content.find_all("tr")
            for black_raw in blacks:
                user_name = black_raw.find("a",class_='avatar_link').text.strip()
                black_list.append(user_name)
        except KeyError:
            log.error("Failed to get black_list of {tb_name}".format(tb_name=tb_name))
            return False,[]

        return has_next,black_list


    def _blacklist_cancels(self,tb_name,names:list):
        """
        解除黑名单
        _blacklist_cancels(tb_name,names:list)

        参数:
            names: 列表 用户名或昵称的列表
        """
        payload = [('ie','utf-8'),('word',tb_name),('tbs',self._get_tbs())]
        count = 0
        for name in names:
            if name and type(name) == str:
                user_id = self._name2userid(name)
                if user_id:
                    payload.append(('list[]',self._name2userid(name)))
                    count+=1
        if not count:
            return False

        self._set_host(self.api.blacklist_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.blacklist_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Delete {names} from black list in {tb_name}".format(names=names,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to delete {names} from black list in {tb_name}".format(names=names,tb_name=tb_name))
        return False


    def _blacklist_cancel(self,tb_name,name):
        """
        解除黑名单
        _blacklist_add(tb_name,name)

        参数:
            name: 字符串 用户名或昵称
        """
        if tb_name and name:
            return self._blacklist_cancels(tb_name,[str(name),])
        else:
            return False


    def _recovers(self,tb_name,tid_pids:list):
        """
        批量恢复帖子
        _recovers(tb_name,tid_pids:list)

        参数:
            tid_pids: 列表 由元组(tid,pid)组成的列表
        """
        payload = {'ie':'utf-8',
                   'word':tb_name,
                   'tbs':self._get_tbs(),
                   }
        count = 0
        for count,tid_pid in enumerate(tid_pids):
            if type(tid_pid) == list or type(tid_pid) == tuple:
                try:
                    tid,pid = tid_pid
                    if not tid:
                        continue
                except (ValueError):
                    log.error("Too many values to unpack in {item}".format(item=tid_pid))
                    continue
            else:
                tid = tid_pid
                if not tid:
                    continue
                pid = '0'
            payload['list[{count}][thread_id]'.format(count=count)] = tid
            payload['list[{count}][post_id]'.format(count=count)] = pid
            payload['list[{count}][post_type]'.format(count=count)] = 0 if int(pid) == 0 else 1
        if not count:
            return False

        self._set_host(self.api.recover_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.recover_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Recover tid:{tid} pid:{pid}".format(tid=tid,pid=pid))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to recover tid:{tid} pid:{pid}".format(tid=tid,pid=pid))
        return False


    def _recover(self,tb_name,tid,pid = 0):
        """
        恢复帖子
        _recover(tb_name,tid,pid=0)
        """
        if tb_name and tid:
            return self._recovers(tb_name,[(tid,pid),])
        else:
            return False
    

    def _unblock_users(self,tb_name,names:list):
        """
        批量解封用户
        _unblock_users(tb_name,names:list)

        参数:
            names: 列表 用户名或昵称的列表
        """
        payload = {'ie':'utf-8',
                   'word':tb_name,
                   'tbs':self._get_tbs(),
                   'type':0
                   }
        count = 0
        for name in names:
            if name:
                user_id = self._name2userid(name)
                if user_id:
                    payload['list[{count}][user_id]'.format(count=count)] = user_id
                    payload['list[{count}][user_name]'.format(count=count)] = name
                    count+=1
        if not count:
            return False

        self._set_host(self.api.unblock_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.unblock_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Unblock {names} in {tb_name}".format(names=names,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to unblock {names} in {tb_name}".format(names=names,tb_name=tb_name))
        return False


    def _unblock_user(self,tb_name,name):
        """
        解封用户
        _unblock_user(tb_name,name)

        参数:
            name:str 用户名或昵称
        """
        if tb_name and name:
            return self._unblock_users(tb_name,[str(name),])
        else:
            return False


    def _good_add(self,tb_name,tid,cid = 0):
        """
        加精
        _good_add(tb_name,tid,cid=0)

        参数：
            cid: 整型 未分类为0，分区从右向左自1开始依次递增，最右为1
        """
        if not (tid or tb_name):
            return False

        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid,
                   'cid':cid
                   }

        self._set_host(self.api.good_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.good_add_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Add good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to add good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _good_cancel(self,tb_name,tid):
        """
        撤销加精
        _good_cancel(tb_name,tid)
        """
        if not (tid or tb_name):
            return False

        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid
                   }

        self._set_host(self.api.good_cancel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.good_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Cancel good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to cancel good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _top_set(self,tb_name,tid,use_vip = True):
        """
        设置置顶
        _top_set(self,tb_name,tid,is_vip=True)

        参数:
            is_vip: 布尔 是否使用会员置顶
        """
        if not (tid or tb_name):
            return False

        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid
                   }
        if use_vip and self._is_self_vip():
            api = self.api.top_vipadd_api
            payload['props_id'] = 1180001
        else:
            use_vip = False
            api = self.api.top_add_api

        self._set_host(api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Success top {tid} in {tb_name} with vip:{vip}".format(tid=tid,tb_name=tb_name,vip=use_vip))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _top_cancel(self,tb_name,tid):
        """
        取消置顶
        _top_cancel(self,tb_name,tid)
        """
        if not (tid or tb_name):
            return False

        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._tbname2fid(tb_name),
                   'tid':tid
                   }

        self._set_host(self.api.top_vipcancel_api)
        retry_times = 2
        while retry_times:
            try:
                res = req.post(self.api.top_vipcancel_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    break
            retry_times-=1

        self._set_host(self.api.top_cancel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.top_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    log.info("Success cancel top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to cancel top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _add_admin(self,tb_name,name,cid = 0):
        """
        添加吧务
        _add_admin(tb_name,name,cid=0)

        参数:
            cid: 整型 序号代表待添加类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']
        """
        if self._is_nick_name(name):
            return False

        types = ['assist','picadmin','voiceadmin','videoadmin','broadcast_admin']
        try:
            cid = int(cid)
            _type = types[cid]
        except (ValueError):
            log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
            return False
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'word':tb_name,
                   'type':_type,
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.api.admin_add_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(self.api.admin_add_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Success add admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to add admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
        return False


    def _del_admin(self,tb_name,name,cid = 0):
        """
        删除吧务
        _del_admin(tb_name,name,cid=0)

        参数:
            cid: 整型 序号代表待删除类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']
        """
        if self._is_nick_name(name):
            return False

        types = ['assist','picadmin','voiceadmin','videoadmin','broadcast_admin']
        try:
            cid = int(cid)
            _type = types[cid]
        except (ValueError):
            log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
            return False
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'word':tb_name,
                   'type':_type,
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.api.admin_del_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(self.api.admin_del_api,
                               data = payload,
                               headers = self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    log.info("Success delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
        return False


    def _refuse_appeals(self,tb_name):
        """
        拒绝吧内所有申诉
        """

        def __appeal_handle(appeal_id,refuse = True):
            """
            拒绝或通过申诉
            __appeal_handle(appeal_id,refuse=True)

            参数:
                appeal_id: 整型 申诉请求的编号
                refuse: 布尔 是否拒绝申诉
            """
            payload = {'status':2 if refuse else 1,
                       'reason':'null',
                       'tbs':self._get_tbs(),
                       'appeal_id':appeal_id,
                       'forum_id':self._tbname2fid(tb_name),
                       'ie':'gbk'
                       }

            self._set_host(self.api.appeal_handle_api)
            retry_times = 5
            while retry_times:
                try:
                    res = req.post(self.api.appeal_handle_api,
                                   data = payload,
                                   headers = self.account.headers)
                except req.exceptions.RequestException:
                    pass
                else:
                    if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                        log.info("Success handle {appeal_id} in {tb_name}, refuse:{refuse}".format(appeal_id=appeal_id,tb_name=tb_name,refuse=refuse))
                        return True
                retry_times-=1
                time.sleep(0.25)

            log.warning("Failed to handle {appeal_id} in {tb_name}, refuse:{refuse}".format(appeal_id=appeal_id,tb_name=tb_name,refuse=refuse))
            return False

        def __get_appeal_list(pn = 1):
            """
            获取吧申诉列表
            __get_appeal_list(pn=1)

            参数:
                pn: 整型 页数
            """
            params = {'forum_id':self._tbname2fid(tb_name),
                      'page':pn
                      }
            self._set_host(self.api.appeal_list_api)
            retry_times = 5
            while retry_times:
                try:
                    res = req.get(self.api.appeal_list_api,
                                  params = params,
                                  headers = self.account.headers)
                except req.exceptions.RequestException:
                    pass
                else:
                    if res.status_code == 200:
                        raw = res.text
                        break
                retry_times-=1
                time.sleep(0.5)

            try:
                main_json = json.loads(raw,strict=False)
                if int(main_json['errno']):
                    raise(ValueError('error_code is not 0'))
            except (json.JSONDecodeError,ValueError):
                log.error("Failed to get appeal_list of {tb_name}".format(tb_name=tb_name))
                return False,[]

            if int(main_json['pageInfo']['totalPage']):
                has_next = True
            else:
                has_next = False

            appeal_ids = [int(raw['appeal_id']) for raw in main_json['appealRecordList']]

            return has_next,appeal_ids

        has_next = True
        while has_next:
            has_next,appeal_ids = __get_appeal_list()
            for appeal_id in appeal_ids:
                __appeal_handle(appeal_id)