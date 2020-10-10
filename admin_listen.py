#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

from collections import deque

import re
import browser



PATH = os.path.split(os.path.realpath(sys.argv[0]))[0]



class TimeRange(object):
    """
    时间范围记录

    TimeRange(queue_len=2,init_time=None)
    """


    __slots__ = ('time_queue',
                 'lower','upper')

    today = time.localtime().tm_mday


    def __init__(self,queue_len=2,init_time=None):
        if queue_len < 2:
            queue_len = 2
        recent_time = init_time if init_time else time.time()
        self.time_queue = deque([recent_time] * queue_len,maxlen=queue_len)
        self.lower = recent_time
        self.upper = recent_time


    @staticmethod
    def is_today():
        if TimeRange.today == time.localtime().tm_mday:
            return True
        else:
            return False


    def append(self,new=None):
        self.lower = self.time_queue.popleft()
        self.upper = self.time_queue[0]
        if new:
            self.time_queue.append(new)
        else:
            self.time_queue.append(time.time())


    def is_inrange(self,check_time):
        if self.lower < check_time <= self.upper:
            return True
        else:
            return False



class Listener(object):


    __slots__ = ('listener','admin',
                 'tb_name','tb_name_eng',
                 'listen_tid',
                 'time_range','func_map')


    access_user = {'kk不好玩':3,'荧光_Starry':3,'5b8uvxe':3,
                   '给对方v抄':2,'天下皆是老婆':2,'摩尔迦娜':2,'陌寒大大233':2,'BSDS集团':2,'呵呵2001111':2,'白菜仙尊':2,'此用户未取名字':2,
                   '丶阳光刺穿心_':2,'Miragari':2,'有栖kiss':2,
                   '物语粉穹妹迷':1,'甜酒味的巷子口':1,'人族步兵凶凶的':1,'木卡夕':1,'847682701':1,'缔结哟':1,'勤奋的Mr陈':1,'未知错误已发生':1,
                   '批评家之死':1,'议会记录者':1,'10Emmanuel10':1,'ARNOLawsky':1,'MinatoChen':1,'Mafia文':1,'灵魂震荡s':1,
                   '赋闲在家吃':1,'安柒ゝ莫莫莫':1,'银星glimmer':1}


    def __init__(self,admin_BDUSS_key,listener_BDUSS_key,tb_name,tb_name_eng,listen_tid):
        self.listener = browser.AdminBrowser(arg.listener_BDUSS_key)
        self.admin = browser.CloudReview(arg.admin_BDUSS_key,tb_name,tb_name_eng)

        self.tb_name = tb_name
        self.tb_name_eng = tb_name_eng
        self.listen_tid = listen_tid

        self.time_range = TimeRange(2,0.1)
        #self.time_range = TimeRange()

        self.func_map = {'recommend':self.cmd_recommend,
                         'drop':self.cmd_drop,
                         'unblock':self.cmd_unblock,
                         'block':self.cmd_block,
                         'recover':self.cmd_recover,
                         'blacklist_add':self.cmd_blacklist_add,
                         'blacklist_cancel':self.cmd_blacklist_cancel,
                         'mysql_white':self.cmd_mysql_white,
                         'mysql_black':self.cmd_mysql_black,
                         'mysql_delete':self.cmd_mysql_delete
                         }


    def quit(self):
        self.listener.quit()
        self.admin.quit()


    def _prase_cmd(self,text):
        """
        解析指令
        """

        if not text.startswith('@'):
            return '',''

        cmd = re.sub('^@.*? ','',text).strip()
        cmds = cmd.split(' ',1)

        if len(cmds) == 1:
            cmd_type = cmds[0]
            arg = ''
        elif len(cmds) == 2:
            cmd_type = cmds[0]
            arg = cmds[1]
        else:
            cmd_type = ''
            arg = ''

        return cmd_type,arg


    @staticmethod
    def get_id(url):
        """
        从指令链接中找出tid和pid
        """

        tid_raw = re.search('(/p/|tid=|thread_id=)(\d+)',url)
        tid = int(tid_raw.group(2)) if tid_raw else 0

        pid_raw = re.search('(pid|post_id)=(\d+)',url)
        pid = int(pid_raw.group(2)) if pid_raw else 0

        return tid,pid


    def scan(self):
        self.time_range.append()
        ats = self.listener.get_self_ats()

        need_post = False
        if ats:
            for end_index,at in enumerate(ats):
                if not self.time_range.is_inrange(at.create_time):
                    ats = ats[:end_index]
                    break
                if at.tid == self.listen_tid:
                    need_post = True

        if need_post:
            posts = self.listener.get_posts(self.listen_tid,9999)
            post_map = {post.pid:post for post in posts if post.floor != 1}
        else:
            post_map = {}

        for at in ats:

            obj = post_map.get(at.pid,at)

            flag = self._handle_cmd(obj)
            if flag is True:
                self.admin.del_post(self.tb_name,obj.tid,obj.pid)
            elif flag is False:
                self.listener.del_post(self.tb_name,obj.tid,obj.pid)


    def _handle_cmd(self,obj):

        cmd_type,arg = self._prase_cmd(obj.text)
        func = self.func_map.get(cmd_type,self.cmd_default)
        return func(obj,arg)


    def cmd_recommend(self,at,arg):
        """
        recommend指令
        对指令所在主题帖执行“大吧主首页推荐”操作

        权限: 1
        限制: 监听帖禁用
        """

        if at.tid == self.listen_tid:
            return False
        if at.tb_name != self.tb_name:
            return None
        if self.access_user.get(at.user.user_name,0) < 1:
            return None

        browser.log.info("{user}: {cmd} in tid:{tid}".format(user=at.user.user_name,cmd=at.text,tid=at.tid))

        if self.admin.recommend(self.tb_name,at.tid):
            return True
        else:
            return None


    def cmd_drop(self,at,arg):
        """
        drop指令
        删除指令所在主题帖并封禁楼主十天
        
        权限: 2
        限制: 监听帖禁用
        """

        if at.tid == self.listen_tid:
            return False
        if at.tb_name != self.tb_name:
            return None
        if self.access_user.get(at.user.user_name,0) < 2:
            return None

        browser.log.info("{user}: {cmd} in tid:{tid}".format(user=at.user.user_name,cmd=at.text,tid=at.tid))

        posts = self.listener.get_posts(at.tid)
        if not posts:
            return None

        browser.log.info("Try to delete thread {text} post by {user_name}/{nick_name}".format(text=posts[0].text,user_name=posts[0].user.user_name,nick_name=posts[0].user.nick_name))

        self.admin.block(posts[0].user,self.tb_name,day=10)
        self.admin.del_post(self.tb_name,at.tid,at.pid)
        self.admin.del_thread(self.tb_name,at.tid)

        return None


    def cmd_unblock(self,post,user_name):
        """
        unblock指令
        通过用户名解封用户

        权限: 2
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 2:
            return False
        if not user_name:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        return self.admin.unblock_user(self.tb_name,user_name)


    def cmd_block(self,post,user_name):
        """
        block指令
        通过用户名封禁用户

        权限: 2
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 2:
            return False
        if not user_name:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        user = browser.UserInfo()
        user.user_name = user_name
        return self.admin.block(user,self.tb_name,day=10)[0]


    def cmd_recover(self,post,url):
        """
        recover指令
        恢复链接所指向的帖子

        权限: 2
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 2:
            return False
        if not url:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        tid,pid = self.get_id(url)
        if not tid:
            return False

        posts = self.listener.get_posts(tid)
        if not posts:
            pid = 0

        if pid and self.admin.mysql.ping():
            self.admin.mysql.add_pid(pid)

        return self.admin.recover(self.tb_name,tid,pid)


    def cmd_blacklist_add(self,post,url):
        """
        blacklist_add指令
        将链接所指向的主题帖的楼主加入贴吧黑名单

        权限: 3
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 3:
            return False
        if not url:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        tid = self.get_id(url)[0]
        if not tid:
            return False

        posts = self.listener.get_posts(tid)
        if not posts:
            return False

        user = posts[0].user
        name = user.user_name if user.user_name else user.nick_name
        return self.admin.blacklist_add(self.tb_name,name)


    def cmd_blacklist_cancel(self,post,url):
        """
        blacklist_cancel指令
        将链接所指向的主题帖的楼主移出贴吧黑名单

        权限: 3
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 3:
            return False
        if not url:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        tid = self.get_id(url)[0]
        if not tid:
            return False

        posts = self.listener.get_posts(tid)
        if not posts:
            return False

        user = posts[0].user
        name = user.user_name if user.user_name else user.nick_name
        return self.admin.blacklist_cancel(self.tb_name,name)


    def cmd_mysql_white(self,post,url):
        """
        mysql_white指令
        将链接所指向的主题帖的楼主加入脚本白名单

        权限: 3
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 3:
            return False
        if not url:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        tid = self.get_id(url)[0]
        if not tid:
            return False

        posts = self.listener.get_posts(tid)
        if not posts:
            return False

        if not self.admin.mysql.ping():
            browser.log.error("Failed to excute!")
            return False

        return self.admin.add_portrait(portrait=posts[0].user.portrait,user_name=posts[0].user.user_name,mode=True)


    def cmd_mysql_black(self,post,url):
        """
        mysql_black指令
        将链接所指向的主题帖的楼主加入脚本黑名单

        权限: 3
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 3:
            return False
        if not url:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        tid = self.get_id(url)[0]
        if not tid:
            return False

        posts = self.listener.get_posts(tid)
        if not posts:
            return False

        if not self.admin.mysql.ping():
            browser.log.error("Failed to excute!")
            return False

        return self.admin.add_portrait(portrait=posts[0].user.portrait,user_name=posts[0].user.user_name,mode=False)


    def cmd_mysql_delete(self,post,user_name):
        """
        mysql_delete指令
        清除用户名对应的脚本黑/白名单状态

        权限: 3
        限制: 仅在监听帖可用
        """

        if post.tid != self.listen_tid:
            return None
        if self.access_user.get(post.user.user_name,0) < 3:
            return False
        if not user_name:
            return False

        browser.log.info("{user}: {cmd}".format(user=post.user.user_name,cmd=post.text))

        if not self.admin.mysql.ping():
            browser.log.error("Failed to excute!")
            return False

        return self.admin.del_portrait(user_name=user_name)


    def cmd_default(self,obj,arg):
        """
        default指令
        """

        if obj.tid == self.listen_tid:
            return False
        else:
            return None



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='大吧主放权脚本',allow_abbrev=False)
    parser.add_argument('--admin_BDUSS_key','-ak',
                        type=str,
                        default='default',
                        help='作为键值从user_control/BDUSS.json中取出BDUSS，该BDUSS为对应吧的大吧主')
    parser.add_argument('--listener_BDUSS_key','-lk',
                        type=str,
                        default='listener',
                        help='作为键值从user_control/BDUSS.json中取出BDUSS，该BDUSS为监听者')

    parser.add_argument('--tb_name','-b',
                        type=str,
                        help='执行大吧主操作的贴吧名',
                        required=True)
    parser.add_argument('--tb_name_eng','-be',
                        type=str,
                        help='执行大吧主操作的贴吧英文名，用于链接MySQL',
                        required=True)

    parser.add_argument('--listen_tid','-t',
                        type=int,
                        help='监听帖子的tid',
                        metavar='TID',
                        required=True)
    arg = parser.parse_args()

    listener = Listener(**vars(arg))

    while TimeRange.is_today():
        listener.scan()
        time.sleep(10)
        browser.log.debug('heartbeat')

    listener.quit()