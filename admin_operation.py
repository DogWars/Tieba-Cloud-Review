#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
JSON Example:
{
  "tb_name": "有米的日子",

  //[tid,[tid,pid]]
  "recover": [],

  //[name,]
  "unblock": [],

  //[name,]
  "blacklist_add": [],

  //[name,]
  "blacklist_cancel": [],

  //[tid,[tid,cid=0],]
  "good_add": [],

  //[tid,]
  "good_cancel": [],

  //[tid,[tid,use_vip=true],]
  "top_set": [],

  //[tid,]
  "top_cancel": []
}
"""



import os
import argparse

import re
import json
import browser



PATH = os.path.split(os.path.realpath(__file__))[0]



def _run_task(json_str):
    """
    运行json文件指定的任务
    """

    note = re.search('/\*.*\*/',json_str,re.S)
    if note:
        note = note.group()
    else:
        note = ''
    json_str = json_str.replace(note,'')
    task_control = json.loads(json_str)


    tb_name = task_control['tb_name']


    tid_pids = task_control.get('recover',[])
    if tid_pids:
        if brow.recovers(tb_name,tid_pids):
            task_control['recover'] = []


    unblocks = task_control.get('unblock',[])
    if unblocks:
        if brow.unblock_users(tb_name,unblocks):
            task_control['unblock'] = []


    blacklist_adds = task_control.get('blacklist_add',[])
    temp = []
    for name in blacklist_adds:
        if not brow.blacklist_add(tb_name,name):
            temp.append(name)
    task_control['blacklist_add'] = temp


    blacklist_cancels = task_control.get('blacklist_cancel',[])
    if brow.blacklist_cancels(tb_name,blacklist_cancels):
        task_control['blacklist_cancel'] = []

    temp = []
    for item in task_control.get('good_add',[]):
        if type(item) == list:
            if len(item) == 2:
                if not brow.good_add(tb_name,item[0],item[1]):
                    temp.append(item)
            else:
                browser.log.error('Wrong length of {item}'.format(item=item))
        else:
            if not brow.good_add(tb_name,item):
                temp.append(item)
    task_control['good_add'] = temp


    temp = []
    for tid in task_control.get('good_cancel',[]):
        if not brow.good_cancel(tb_name,tid):
            temp.append(tid)
    task_control['good_cancel'] = temp


    temp = []
    for item in task_control.get('top_set',[]):
        if type(item) == list:
            if len(item) == 2:
                if not brow.top_set(tb_name,item[0],item[1]):
                    temp.append(item)
            else:
                browser.log.error('Wrong length of {item}'.format(item=item))
        else:
            if not brow.top_set(tb_name,item):
                temp.append(item)
    task_control['top_set'] = temp


    temp = []
    for tid in task_control.get('top_cancel',[]):
        if not brow.top_cancel(tb_name,tid):
            temp.append(tid)
    task_control['top_cancel'] = temp

    if task_control.get('refuse_appeals',False):
        brow.refuse_appeals(tb_name)


    json_str = json.dumps(task_control,ensure_ascii=False,indent=2,separators=(',',':'))
    json_str = json_str + '\n' + note

    return json_str



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='ADMIN OPERATION',allow_abbrev=False)

    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='headers.txt（包含BDUSS的消息头）的路径，默认值为./user_control/headers.txt')
    parser.add_argument('--operation_ctrl_filepath','-oc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='operation_control.json的路径，对example.py而言默认值为./user_control/example.json')

    parser.add_argument('--tieba_name','-b',
                        type=str,
                        help='需要执行大吧主操作的目标贴吧吧名')
    parser.add_argument('--unblock','-u',
                        type=str,
                        help='待解封用户的用户名')
    parser.add_argument('--recover','-r',
                        type=int,
                        nargs='*',
                        help='待恢复帖子的tid(必选)与pid(可选)')

    args = parser.parse_args()

    brow = browser.AdminBrowser(args.header_filepath)


    if args.tieba_name:

        if args.unblock:
            brow.unblock_user(args.tieba_name,args.unblock)
        if args.recover:
            if len(args.recover) == 1:
                brow.recover(args.tieba_name,args.recover[0])
            elif len(args.recover) == 2:
                brow.recover(args.tieba_name,args.recover[0],args.recover[1])
            else:
                browser.log.warning('Wrong format of args --recover')
                pass

    else:

        if os.access(args.operation_ctrl_filepath,os.F_OK | os.R_OK | os.W_OK):
            with open(args.operation_ctrl_filepath,'r',encoding='utf-8-sig') as ctrl_file:
                json_str = ctrl_file.read()
        else:
            browser.log.critical('Permission denied !')
            brow.quit()
            os._exit(-1)

        json_str = _run_task(json_str)

        with open(args.operation_ctrl_filepath,'w',encoding='utf-8-sig') as ctrl_file:
            ctrl_file.write()

    brow.quit()