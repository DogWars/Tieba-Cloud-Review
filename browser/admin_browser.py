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
                 'block_app_api',
                 'block_web_api',

                 'recover_api',
                 'unblock_api',
                 'recommend_api',
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
        self.block_app_api = 'http://c.tieba.baidu.com/c/c/bawu/commitprison'
        self.block_web_api = 'http://tieba.baidu.com/pmc/blockid'

        self.recover_api = 'http://tieba.baidu.com/bawu2/platform/resPost'
        self.unblock_api = 'http://tieba.baidu.com/bawu2/platform/cancelFilter'
        self.recommend_api = 'http://c.tieba.baidu.com/c/c/bawu/pushRecomToPersonalized'

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
    AdminBrowser(self,headers_filepath)

    参数:
        headers_filepath: str 消息头文件路径
    """


    __slots__ = ('api',)


    def __init__(self,headers_filepath):
        super(AdminBrowser,self).__init__(headers_filepath)

        self.api = _Admin_API()


    def quit(self):
        super(AdminBrowser,self).quit()


    def block(self,user,tb_name,day,reason='极光 - 贴吧反广告墙'):
        """
        使用客户端api的封禁，支持小吧主、语音小编封10天
        block(user,tb_name,day,reason='极光 - 贴吧反广告墙')

        参数:
            user: UserInfo类 待封禁用户信息
            tb_name: str 吧名
            day: int 封禁天数
            reason: str 封禁理由（可选）

        返回值:
            flag: bool 操作是否成功
            user: UserInfo类 补充后的用户信息
        """

        if user.user_name:
            un = user.user_name
        elif user.portrait:
            user.user_name,user.nick_name = self._portrait2names(user.portrait)
        elif user.nick_name:
            user.portrait = self._name2portrait(user.nick_name)
        else:
            log.error('Failed to block null in {tb_name}'.format(name=user.user_name,tb_name=tb_name))
            return False,user

        log_name = user.user_name if user.user_name else user.nick_name

        try:
            payload = {'BDUSS':self.account.cookies['BDUSS'],
                       '_client_id':'wappc_1600500414046_633',
                       '_client_type':2,
                       '_client_version':'11.8.8.7',
                       '_phone_imei':'000000000000000',
                       'cuid':self.account.app_headers['cuid'],
                       'cuid_galaxy2':self.account.app_headers['cuid_galaxy2'],
                       'cuid_gid':'',
                       'day':day,
                       'fid':self._tbname2fid(tb_name),
                       'model':'TAS-AN00',
                       'net_type':1,
                       'nick_name':user.nick_name if user.nick_name else user.user_name,
                       'ntn':'banid',
                       'portrait':user.portrait,
                       'post_id':'null',
                       'reason':reason,
                       'stoken':self.account.cookies['STOKEN'],
                       'tbs':self._get_tbs(),
                       'un':user.user_name,
                       'word':tb_name,
                       'z':'6955178525',
                       'z_id':'E90411739518335BA49F4AD85559B3F1CD'
                       }

        except KeyError:
            log.error('Failed to block in {tb_name}'.format(tb_name=tb_name))
            return False,user

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.block_app_api,
                               data=self._app_sign(payload))
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"error_code":"0"',res.content.decode('unicode_escape')):
                    log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=log_name,tb_name=tb_name,day=day))
                    return True,user
            retry_times-=1
            time.sleep(0.25)

        log.error('Failed to block {name} in {tb_name}'.format(name=log_name,tb_name=tb_name))
        return False,user


    def _web_block(self,user,tb_name,day,reason='极光 - 贴吧反广告墙'):
        """
        使用网页版api的封禁，权限不足时无法封禁
        _web_block(user,tb_name,day,reason='default')

        参数:
            user: UserInfo类 待封禁用户信息
            tb_name: str 吧名
            day: int 封禁天数
            reason: str 封禁理由（可选）

        返回值:
            flag: bool 操作是否成功
            user: UserInfo类 补充后的用户信息
        """

        payload = {"ie":"gbk"}
        payload['reason'] = reason

        try:
            payload['day'] = day
            payload['fid'] = self._tbname2fid(tb_name)
            payload['tbs'] = self._get_tbs()
        except KeyError:
            log.error('AttributeError: Failed to block!')

        if user.user_name:
            name = user.user_name
            payload['user_name[]'] = name

        elif user.portrait:
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
                return False,user

        elif user.nick_name:
            name = user.nick_name
            portrait = self._name2portrait(name)
            if not portrait:
                log.error('Failed to block {name} in {tb_name}'.format(name=name,tb_name=tb_name))
                return False,user
            payload['nick_name[]'] = name
            payload['portrait[]'] = portrait
            user.portrait = portrait

        else:
            log.error('Failed to block in {tb_name}'.format(tb_name=tb_name))
            return False,user

        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.block_web_api,
                               data=payload,
                               headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"errno":0',res.content.decode('unicode_escape')):
                    log.info('Success blocking {name} in {tb_name} for {day} days'.format(name=name,tb_name=tb_name,day=payload['day']))
                    return True,user
            retry_times-=1
            time.sleep(0.25)

        log.error('Failed to block {name} in {tb_name}'.format(name=name,tb_name=tb_name))
        return False,user


    def del_thread(self,tb_name,tid):
        """
        删除主题帖
        del_thread(tb_name,tid)

        参数:
            tb_name: str 帖子所在的贴吧名
            tid: int 待删除的主题帖tid

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def del_threads(self,tb_name,tids):
        """
        批量删除主题帖
        del_threads(tb_name,tids)

        参数:
            tb_name: str 帖子所在的贴吧名
            tids: list(int) 待删除的主题帖tid列表

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def del_post(self,tb_name,tid,pid):
        """
        删除回复
        del_post(tb_name,tid,pid)

        参数:
            tb_name: str 帖子所在的贴吧名
            tid: int 回复所在的主题帖tid
            pid: int 待删除的回复pid

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def blacklist_add(self,tb_name,name):
        """
        添加用户至黑名单
        blacklist_add(tb_name,name)

        参数:
            tb_name: str 所在贴吧名
            name: str 用户名或昵称

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def blacklist_get(self,tb_name,pn=1):
        """
        获取黑名单列表
        blacklist_get(tb_name,pn=1)

        参数:
            tb_name: str 所在贴吧名
            pn: int 页数

        返回值:
            flag: bool 操作是否成功
            black_list: list(str) 黑名单用户列表
        """

        params = {'word':tb_name,
                  'pn':pn
                  }
        self._set_host(self.api.blacklist_get_api)
        retry_times = 5
        while retry_times:
            try:
                res = req.get(self.api.blacklist_get_api,
                              params=params,
                              headers=self.account.headers)
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


    def blacklist_cancels(self,tb_name,names):
        """
        解除黑名单
        blacklist_cancels(tb_name,names)

        参数:
            tb_name: str 所在贴吧名
            names: list(str) 用户名或昵称的列表

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def blacklist_cancel(self,tb_name,name):
        """
        解除黑名单
        blacklist_cancel(tb_name,name)

        参数:
            tb_name: str 所在贴吧名
            name: str 用户名或昵称

        返回值:
            flag: bool 操作是否成功
        """

        if tb_name and name:
            return self.blacklist_cancels(tb_name,[str(name),])
        else:
            return False


    def recovers(self,tb_name,tid_pids):
        """
        批量恢复帖子
        recovers(tb_name,tid_pids)

        参数:
            tid_pids: list(tuple) 由元组(tid,pid)组成的列表

        返回值:
            flag: bool 操作是否成功
        """

        payload = {'ie':'utf-8',
                   'word':tb_name,
                   'tbs':self._get_tbs(),
                   }
        count = 0
        for tid_pid in tid_pids:
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
            count+=1
        if not count:
            return False

        self._set_host(self.api.recover_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.recover_api,
                               data=payload,
                               headers=self.account.headers)
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


    def recover(self,tb_name,tid,pid=0):
        """
        恢复帖子
        recover(tb_name,tid,pid=0)

        参数:
            tb_name: str 帖子所在的贴吧名
            tid: int 回复所在的主题帖tid
            pid: int 待恢复的回复pid

        返回值:
            flag: bool 操作是否成功
        """

        if tb_name and tid:
            return self.recovers(tb_name,[(tid,pid),])
        else:
            return False
    

    def unblock_users(self,tb_name,names):
        """
        批量解封用户
        unblock_users(tb_name,names)

        参数:
            tb_name: str 所在贴吧名
            names: list(str) 用户名或昵称的列表

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def unblock_user(self,tb_name,name):
        """
        解封用户
        unblock_user(tb_name,name)

        参数:
            tb_name: str 所在贴吧名
            name: str 用户名或昵称
        """

        if tb_name and name:
            return self.unblock_users(tb_name,[str(name),])
        else:
            return False


    def recommend(self,tb_name,tid):
        """
        推荐上首页
        recommend(tb_name,tid)

        参数:
            tb_name: str 帖子所在贴吧名
            tid: int 待推荐的主题帖tid

        返回值:
            flag: bool 操作是否成功
        """

        payload = {'BDUSS':self.account.cookies['BDUSS'],
                   '_client_id':'wappc_1600500414046_633',
                   '_client_type':'2',
                   '_client_version':'11.8.8.7',
                   '_phone_imei':'000000000000000',
                   'c3_aid':self.account.app_headers['c3_aid'],
                   'cuid':self.account.app_headers['cuid'],
                   'cuid_galaxy2':self.account.app_headers['cuid_galaxy2'],
                   'cuid_gid':'',
                   'forum_id':self._tbname2fid(tb_name),
                   'model':'TAS-AN00',
                   'net_type':1,
                   'oaid':'{"sc":-1,"sup":0,"tl":0}',
                   'stoken':self.account.cookies['STOKEN'],
                   'tbs':self._get_tbs(),
                   'thread_id':tid
                   }

        raw = None
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.recommend_api,
                               data=self._app_sign(payload))
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    raw = res.text
                    break
            retry_times-=1
            time.sleep(0.25)

        if not raw:
            return False

        try:
            main_json = json.loads(raw,strict=False)
            if int(main_json['error_code']):
                raise(ValueError('error_code is not 0 ' + main_json['error_msg']))
            if int(main_json['data']['is_push_success']):
                raise(ValueError('is_push_success is not 0 ' + main_json['data']['msg']))
        except (json.JSONDecodeError,ValueError) as err:
            log.error("Failed to recommend {tid} in {tb_name} Reason:{reason}".format(tid=tid,tb_name=tb_name,reason=str(err)))
            return False

        log.info("Recommend {tid} in {tb_name}".format(tid=tid,tb_name=tb_name))
        return True


    def good_add(self,tb_name,tid,cid=0):
        """
        加精
        good_add(tb_name,tid,cid=0)

        参数:
            tb_name: str 帖子所在贴吧名
            tid: int 待加精的主题帖tid
            cid: int 未分类为0，分区从右向左自1开始逐个递增，最右为1

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def good_cancel(self,tb_name,tid):
        """
        撤销加精
        good_cancel(tb_name,tid)

        参数:
            tb_name: str 帖子所在贴吧名
            tid: int 待撤精的主题帖tid

        返回值:
            flag: bool 操作是否成功
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
                               data=payload,
                               headers=self.account.headers)
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


    def top_set(self,tb_name,tid,use_vip=True):
        """
        设置置顶
        top_set(self,tb_name,tid,is_vip=True)

        参数:
            tb_name: str 帖子所在贴吧名
            tid: int 待置顶的主题帖tid
            is_vip: bool 是否使用会员置顶

        返回值:
            flag: bool 操作是否成功
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
        retry_times = 3
        while retry_times:
            try:
                res = req.post(api,
                               data=payload,
                               headers=self.account.headers)
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


    def top_cancel(self,tb_name,tid):
        """
        取消置顶
        top_cancel(self,tb_name,tid)

        参数:
            tb_name: str 帖子所在贴吧名
            tid: int 待撤置顶的主题帖tid

        返回值:
            flag: bool 操作是否成功
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
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.top_vipcancel_api,
                               data=payload,
                               headers=self.account.headers)
            except req.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200 and re.search('"err_code":0',res.content.decode('unicode_escape')):
                    break
            retry_times-=1
            time.sleep(0.25)

        self._set_host(self.api.top_cancel_api)
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.top_cancel_api,
                               data=payload,
                               headers=self.account.headers)
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


    def add_admin(self,tb_name,name,cid=0):
        """
        添加吧务
        add_admin(tb_name,name,cid=0)

        参数:
            tb_name: str 所在贴吧名
            name: str 用户名或昵称
            cid: int 序号代表待添加类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']

        返回值:
            flag: bool 操作是否成功
        """

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
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.admin_add_api,
                               data=payload,
                               headers=self.account.headers)
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


    def del_admin(self,tb_name,name,cid=0):
        """
        删除吧务
        del_admin(tb_name,name,cid=0)

        参数:
            tb_name: str 所在贴吧名
            name: str 用户名或昵称
            cid: int 序号代表待删除类型，对应列表['小吧主','图片小编','语音小编','视频小编','广播小编']

        返回值:
            flag: bool 操作是否成功
        """

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
        retry_times = 3
        while retry_times:
            try:
                res = req.post(self.api.admin_del_api,
                               data=payload,
                               headers=self.account.headers)
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


    def refuse_appeals(self,tb_name):
        """
        拒绝吧内所有解封申诉
        refuse_appeals(self,tb_name)

        参数:
            tb_name: str 所在贴吧名
        """


        def __appeal_handle(appeal_id,refuse=True):
            """
            拒绝或通过解封申诉
            __appeal_handle(appeal_id,refuse=True)

            参数:
                appeal_id: int 申诉请求的编号
                refuse: bool 是否拒绝申诉
            """

            payload = {'status':2 if refuse else 1,
                       'reason':'null',
                       'tbs':self._get_tbs(),
                       'appeal_id':appeal_id,
                       'forum_id':self._tbname2fid(tb_name),
                       'ie':'gbk'
                       }

            self._set_host(self.api.appeal_handle_api)
            retry_times = 3
            while retry_times:
                try:
                    res = req.post(self.api.appeal_handle_api,
                                   data=payload,
                                   headers=self.account.headers)
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


        def __get_appeal_list(pn=1):
            """
            获取吧申诉列表
            __get_appeal_list(pn=1)

            参数:
                pn: int 页数
            """

            params = {'forum_id':self._tbname2fid(tb_name),
                      'page':pn
                      }
            self._set_host(self.api.appeal_list_api)
            retry_times = 5
            while retry_times:
                try:
                    res = req.get(self.api.appeal_list_api,
                                  params=params,
                                  headers=self.account.headers)
                except req.exceptions.RequestException:
                    pass
                else:
                    if res.status_code == 200:
                        raw = res.text
                        break
                retry_times-=1
                time.sleep(0.25)

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