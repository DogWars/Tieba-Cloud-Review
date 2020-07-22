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
import browser



if __name__ == '__main__':

    PATH = os.path.split(os.path.realpath(__file__))[0].replace('\\','/')

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

    control_json :dict = browser._CloudReview._link_ctrl_json(kwargs['operation_ctrl_filepath'])
    tb_name = control_json['tb_name']
    brow = browser.AdminBrowser(kwargs['header_filepath'],10)

    tid_pids = control_json.get('recover',[])
    if tid_pids:
        brow._recovers(tb_name,tid_pids)

    unblocks = control_json.get('unblock',[])
    if unblocks:
        brow._unblock_users(tb_name,unblocks)

    blacklist_adds = control_json.get('blacklist_add',[])
    for name in blacklist_adds:
        brow._blacklist_add(tb_name,name)

    blacklist_cancels = control_json.get('blacklist_add',[])
    brow._blacklist_cancels(tb_name,blacklist_cancels)

    for item in control_json.get('good_add',[]):
        if type(item) == list:
            if len(item) == 2:
                brow._good_add(tb_name,item[0],item[1])
            else:
                brow.log.error('Wrong length of {item}'.format(item=item))
        else:
            brow._good_add(tb_name,item)

    for tid in control_json.get('good_cancel',[]):
        brow._good_cancel(tb_name,tid)

    for item in control_json.get('top_set',[]):
        if type(item) == list:
            if len(item) == 2:
                brow._top_set(tb_name,item[0],item[1])
            else:
                brow.log.error('Wrong length of {item}'.format(item=item))
        else:
            brow._top_set(tb_name,item)

    for tid in control_json.get('top_cancel',[]):
        brow._top_cancel(tb_name,tid)

    brow.quit()