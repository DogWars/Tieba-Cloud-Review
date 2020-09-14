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



if __name__ == '__main__':

    PATH = os.path.split(os.path.realpath(__file__))[0]

    parser = argparse.ArgumentParser(description='ADMIN OPERATION')
    parser.add_argument('--operation_ctrl_filepath','-oc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='path of the operation control json | default value for example.py is ./user_control/example.json')
    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='path of the headers txt | default value is ./user_control/headers.txt')
    kwargs = vars(parser.parse_args())


    brow = browser.AdminBrowser(kwargs['header_filepath'],10)


    if os.access(kwargs['operation_ctrl_filepath'],os.F_OK | os.R_OK | os.W_OK):
        with open(kwargs['operation_ctrl_filepath'],'r',encoding='utf-8-sig') as ctrl_file:
            raw = ctrl_file.read()
    else:
        brow.log.critical('Permission denied !')
        brow.quit()
        os._exit(-1)


    note = re.search('/\*.*\*/',raw,re.S)
    if note:
        note = note.group()
    else:
        note = ''
    raw = raw.replace(note,'')
    task_control = json.loads(raw)


    tb_name = task_control['tb_name']


    tid_pids = task_control.get('recover',[])
    if tid_pids:
        if brow._recovers(tb_name,tid_pids):
            task_control['recover'] = []


    unblocks = task_control.get('unblock',[])
    if unblocks:
        if brow._unblock_users(tb_name,unblocks):
            task_control['unblock'] = []


    blacklist_adds = task_control.get('blacklist_add',[])
    temp = []
    for name in blacklist_adds:
        if not brow._blacklist_add(tb_name,name):
            temp.append(name)
    task_control['blacklist_add'] = temp


    blacklist_cancels = task_control.get('blacklist_cancel',[])
    if brow._blacklist_cancels(tb_name,blacklist_cancels):
        task_control['blacklist_cancel'] = []

    temp = []
    for item in task_control.get('good_add',[]):
        if type(item) == list:
            if len(item) == 2:
                if not brow._good_add(tb_name,item[0],item[1]):
                    temp.append(item)
            else:
                brow.log.error('Wrong length of {item}'.format(item=item))
        else:
            if not brow._good_add(tb_name,item):
                temp.append(item)
    task_control['good_add'] = temp


    temp = []
    for tid in task_control.get('good_cancel',[]):
        if not brow._good_cancel(tb_name,tid):
            temp.append(tid)
    task_control['good_cancel'] = temp


    temp = []
    for item in task_control.get('top_set',[]):
        if type(item) == list:
            if len(item) == 2:
                if not brow._top_set(tb_name,item[0],item[1]):
                    temp.append(item)
            else:
                brow.log.error('Wrong length of {item}'.format(item=item))
        else:
            if not brow._top_set(tb_name,item):
                temp.append(item)
    task_control['top_set'] = temp


    temp = []
    for tid in task_control.get('top_cancel',[]):
        if not brow._top_cancel(tb_name,tid):
            temp.append(tid)
    task_control['top_cancel'] = temp


    raw = json.dumps(task_control,ensure_ascii=False,indent=2,separators=(',',':'))
    with open(kwargs['operation_ctrl_filepath'],'w',encoding='utf-8-sig') as ctrl_file:
        ctrl_file.write(raw + '\n' + note)


    if task_control.get('refuse_appeals',False):
        brow._refuse_appeals(tb_name)


    brow.quit()