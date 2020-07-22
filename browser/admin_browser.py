#!/usr/bin/env python
# -*- coding:utf-8 -*-
__all__ = ('AdminBrowser',)



import time

import re
import pickle

import requests as req

from ._browser import _Browser



class AdminBrowser(_Browser):
    """
    提供百度贴吧管理员相关功能
    AdminBrowser(self,headers_filepath:str,admin_type:int)

    参数:
        headers_filepath: 字符串 消息头文件路径
        admin_type: 整型 吧务权限最高允许的封禁天数
    """


    old_del_api = 'http://tieba.baidu.com/bawu2/postaudit/audit'
    del_post_api = 'http://tieba.baidu.com/f/commit/post/delete'
    del_thread_api = 'https://tieba.baidu.com/f/commit/thread/delete'
    del_threads_api = 'https://tieba.baidu.com/f/commit/thread/batchDelete'
    old_block_api = 'http://c.tieba.baidu.com/c/c/bawu/commitprison'
    new_block_api = 'http://tieba.baidu.com/pmc/blockid'

    recover_api = 'http://tieba.baidu.com/bawu2/platform/resPost'
    unblock_api = 'http://tieba.baidu.com/bawu2/platform/cancelFilter'
    good_add_api = 'https://tieba.baidu.com/f/commit/thread/good/add'
    good_cancel_api = 'https://tieba.baidu.com/f/commit/thread/good/cancel'
    blacklist_add_api = 'http://tieba.baidu.com/bawu2/platform/addBlack'
    blacklist_cancel_api = 'http://tieba.baidu.com/bawu2/platform/cancelBlack'
    top_add_api = 'https://tieba.baidu.com/f/commit/thread/top/add'
    top_vipadd_api = 'https://tieba.baidu.com/f/commit/thread/top/madd'
    top_cancel_api = 'https://tieba.baidu.com/f/commit/thread/top/cancel'
    top_vipcancel_api = 'https://tieba.baidu.com/f/commit/thread/top/mcancel'
    admin_add_api='http://tieba.baidu.com/bawu2/platform/addBawuMember'
    admin_del_api='http://tieba.baidu.com/bawu2/platform/delBawuMember'


    def __init__(self,headers_filepath:str,admin_type:int):
        super(AdminBrowser,self).__init__(headers_filepath)
        try:
            self.admin_type = admin_type if admin_type in [1,10] else 1
        except AttributeError:
            raise(AttributeError('Incorrect format!'))

        self.old_block_content = {'BDUSS':self.account.cookies['BDUSS'],
                                  'day':1,
                                  'fid':'',
                                  'ntn':'banid',
                                  'reason':'null',
                                  'tbs':'',
                                  'un':'',
                                  'word':'',
                                  'z':'4623534287'}


    def quit(self):
        super(AdminBrowser,self).quit()


    def _old_block(self,block):
        """
        使用旧版api的封禁，适用于权限不足的情况，且被封禁用户必须有用户名
        """
        try:
            self.old_block_content['day'] = block['day']
            self.old_block_content['fid'] = self._get_fid(block['tb_name'])
            self.old_block_content['tbs'] = self._get_tbs()
            self.old_block_content['un'] = block['user_name']
            self.old_block_content['word'] = block['tb_name']
        except AttributeError:
            self.log.error('AttributeError: Failed to block!')

        self.old_block_content = self._app_sign(self.old_block_content)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.old_block_api,
                               data=self.old_block_content)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"error_code":"0"',res.content.decode('unicode_escape')):
                    self.log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=block['user_name'],tb_name=block['tb_name'],day=self.old_block_content['day']))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning('Failed to block {name} in {tb_name}'.format(name=block['user_name'],tb_name=block['tb_name']))
        return False


    def _new_block(self,block,name_type:str='username'):
        """
        使用新版api的封禁，适用于权限充足或需要封禁无用户名用户（仅有带emoji昵称）的情况
        """
        new_block_content = {"ie":"gbk"}
        new_block_content['reason'] = block['reason'] if block.__contains__('reason') else 'null'

        try:
            new_block_content['day'] = block['day'] if block['day'] < self.admin_type else self.admin_type
            new_block_content['fid'] = self._get_fid(block['tb_name'])
            new_block_content['tbs'] = self._get_tbs()
        except AttributeError:
            self.log.error('AttributeError: Failed to block!')

        if block.get('user_name',''):
            name = block['user_name']
            new_block_content['user_name[]'] = block['user_name']
        elif block.get('nick_name',''):
            name = block['nick_name']
            new_block_content['nick_name[]'] = block['nick_name']
            if block.get('portrait',''):
                new_block_content['portrait[]'] = block['portrait']
            else:
                try:
                    new_block_content['portrait[]'] = self._get_portrait(name)
                except AttributeError:
                    self.log.warning('{user_name}已被屏蔽'.format(user_name=name))
                    return True
        else:
            self.log.warning('Failed to block in {tb_name}'.format(tb_name=block['tb_name']))
            return False

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.new_block_api,
                               data=new_block_content,
                               headers=self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"errno":0',res.content.decode('unicode_escape')):
                    self.log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=name,tb_name=block['tb_name'],day=new_block_content['day']))
                    return True
            retry_times-=1
            time.sleep(0.25)


        self.log.warning('Failed to block {name} in {tb_name}'.format(name=name,tb_name=block['tb_name']))
        return False


    def block(self,block):
        """
        根据需求自动选择api进行封禁，以新版api为优先选择
        block(self,block)

        参数:
            block:封禁请求
                举例: 
                {'tb_name':'吧名',
                'user_name':'用户名',
                'nick_name':'昵称',
                'day':'封禁天数,
                'portrait':'portrait（可选）',
                'reason':'封禁理由（可选）'
                }
        """

        if block['day'] > self.admin_type and block['user_name']:
            self._old_block(block)
        else:
            self._new_block(block)


    def _del_thread(self,tb_name,tid):
        """
        新api，删主题帖
        _del_thread(tb_name,tid)
        """
        payload = {'commit_from':'pb',
                   'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._get_fid(tb_name),
                   'tid':tid
                   }
        self._set_host(self.del_thread_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.del_thread_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to delete thread {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _del_threads(self,tb_name,tids):
        """
        批量删除主题帖
        _del_threads(tb_name,tids)
        """
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'kw':tb_name,
                   'fid':self._get_fid(tb_name),
                   'tid':'_'.join([str(tid) for tid in tids]),
                   'isBan':0
                   }
        self._set_host(self.del_threads_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.del_threads_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Success delete thread {tids} in {tb_name}".format(tids=tids,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to delete thread {tids} in {tb_name}".format(tids=tids,tb_name=tb_name))
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
                   'fid':self._get_fid(tb_name),
                   'tid':tid,
                   'is_vipdel':0,
                   'pid':pid,
                   'is_finf':'false'
                   }
        self._set_host(self.del_post_api)

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.del_post_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to delete post {pid} in {tid} in {tb_name}".format(pid=pid,tid=tid,tb_name=tb_name))
        return False


    def _blacklist_add(self,tb_name,name):
        """
        添加用户至黑名单
        _blacklist_add(tb_name,name)

        参数:
            name: 字符串 用户名或昵称
        """
        if not (tid or tb_name):
            return False

        name = str(name)
        payload = {'ie':'utf-8',
                   'word':tb_name,
                   'tbs':self._get_tbs(),
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.blacklist_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.blacklist_add_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Add {name} to black list in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to add {name} to black list in {tb_name}".format(name=name,tb_name=tb_name))
        return False


    def _blacklist_cancels(self,tb_name,names:list):
        """
        解除黑名单
        _blacklist_add(tb_name,names:list)

        参数:
            names: 列表 用户名或昵称的列表
        """
        payload = [('ie','utf-8'),('word',tb_name),('tbs',self._get_tbs())]
        count = 0
        for name in names:
            if name and type(name) == str:
                user_id = self._get_user_id(name)
                if user_id:
                    payload.append(('list[]',self._get_user_id(name)))
                    count+=1
        if not count:
            return False

        self._set_host(self.blacklist_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.blacklist_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Delete {names} from black list in {tb_name}".format(names=names,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to delete {names} from black list in {tb_name}".format(names=names,tb_name=tb_name))
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
                except(ValueError):
                    self.log.error("Too many values to unpack in {item}".format(item=tid_pid))
                    continue
            else:
                tid = tid_pid
                if not tid:
                    continue
                pid = '0'
            payload['list[{count}][thread_id]'.format(count=count)] = tid
            payload['list[{count}][post_id]'.format(count=count)] = pid
            payload['list[{count}][post_type]'.format(count=count)] = 0 if str(pid) == '0' else 1
        if not count:
            return False

        self._set_host(self.recover_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.recover_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Recover tid:{tid} pid:{pid}".format(tid=tid,pid=pid))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to recover tid:{tid} pid:{pid}".format(tid=tid,pid=pid))
        return False


    def _recover(self,tb_name,tid,pid=0):
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
                user_id = self._get_user_id(name)
                if user_id:
                    payload['list[{count}][user_id]'.format(count=count)] = user_id
                    payload['list[{count}][user_name]'.format(count=count)] = name
                    count+=1
        if not count:
            return False

        self._set_host(self.unblock_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.unblock_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Unblock {names} in {tb_name}".format(names=names,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to unblock {names} in {tb_name}".format(names=names,tb_name=tb_name))
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


    def _good_add(self,tb_name,tid,cid=0):
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
                   'fid':self._get_fid(tb_name),
                   'tid':tid,
                   'cid':cid
                   }

        self._set_host(self.good_add_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.good_add_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Add good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to add good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
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
                   'fid':self._get_fid(tb_name),
                   'tid':tid
                   }

        self._set_host(self.good_cancel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.good_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Cancel good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to cancel good {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _top_set(self,tb_name,tid,use_vip=True):
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
                   'fid':self._get_fid(tb_name),
                   'tid':tid
                   }
        if use_vip and self._is_self_vip():
            api = self.top_vipadd_api
            payload['props_id'] = 1180001
        else:
            use_vip = False
            api = self.top_add_api

        self._set_host(api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Success top {tid} in {tb_name} with vip:{vip}".format(tid=tid,tb_name=tb_name,vip=use_vip))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
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
                   'fid':self._get_fid(tb_name),
                   'tid':tid
                   }

        self._set_host(self.top_vipcancel_api)
        retry_times = 2
        while retry_times:
            try:
                res = req.post(self.top_vipcancel_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    break
            retry_times-=1

        self._set_host(self.top_cancel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.top_cancel_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    self.log.info("Success cancel top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to cancel top {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return False


    def _add_admin(self,tb_name,name,cid=0):
        """
        添加吧务
        _add_admin(tb_name,name,cid=0)

        参数:
            cid: 整型 序号代表待添加类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']
        """
        if self._is_nick_name(name):
            return False

        types=['assist','picadmin','voiceadmin','videoadmin','broadcast_admin']
        try:
            cid=int(cid)
            _type=types[cid]
        except(ValueError):
            self.log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
            return False
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'word':tb_name,
                   'type':_type,
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.admin_add_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(self.admin_add_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Success add admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to add admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
        return False


    def _del_admin(self,tb_name,name,cid=0):
        """
        删除吧务
        _del_admin(tb_name,name,cid=0)

        参数:
            cid: 整型 序号代表待删除类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']
        """
        if self._is_nick_name(name):
            return False

        types=['assist','picadmin','voiceadmin','videoadmin','broadcast_admin']
        try:
            cid=int(cid)
            _type=types[cid]
        except(ValueError):
            self.log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
            return False
        payload = {'ie':'utf-8',
                   'tbs':self._get_tbs(),
                   'word':tb_name,
                   'type':_type,
                   'user_id':self._get_user_id(name)
                   }

        self._set_host(self.admin_del_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.post(self.admin_del_api,
                               data = payload,
                               headers = self.account.headers)
            except(req.exceptions.RequestException):
                pass
            else:
                if res.status_code == 200 and re.search('success',res.content.decode('unicode_escape')):
                    self.log.info("Success delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
                    return True
            retry_times-=1
            time.sleep(0.25)

        self.log.warning("Failed to delete admin {name} in {tb_name}".format(name=name,tb_name=tb_name))
        return False