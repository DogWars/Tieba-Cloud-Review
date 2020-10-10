#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import argparse

import re
import browser



PATH = os.path.split(os.path.realpath(__file__))[0]



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='ADMIN OPERATION',allow_abbrev=False)

    parser.add_argument('tieba_name',
                        type=str,
                        help='需要执行大吧主操作的目标贴吧吧名')
    parser.add_argument('--BDUSS_key','-k',
                        type=str,
                        default='default',
                        help='作为键值从user_control/BDUSS.json中取出BDUSS')

    parser.add_argument('--block','-b',
                        type=str,
                        nargs='+',
                        help='待封10天的用户名/portrait',
                        metavar='STR')
    parser.add_argument('--unblock','-u',
                        type=str,
                        nargs='+',
                        help='待解封的用户名/昵称',
                        metavar='NAME')
    parser.add_argument('--recover','-r',
                        type=int,
                        nargs='+',
                        help='待恢复帖子的tid(必选)与pid(可选)',
                        metavar='ID')
    parser.add_argument('--blacklist_add','-ba',
                        type=str,
                        nargs='+',
                        help='待加黑名单的用户名/昵称列表',
                        metavar='NAME')
    parser.add_argument('--blacklist_cancel','-bc',
                        type=str,
                        nargs='+',
                        help='待解黑名单的用户名/昵称列表',
                        metavar='NAME')

    parser.add_argument('--good_add','-ga',
                        type=int,
                        nargs='+',
                        help='待加精帖子的tid(必选)与目标分类cid(可选)',
                        metavar='ID')
    parser.add_argument('--recommand','-rc',
                        type=int,
                        nargs='+',
                        help='待推荐帖子的tid列表',
                        metavar='TID')

    parser.add_argument('--refuse_appeals','-ra',
                        action='store_true',
                        help='是否拒绝所有申诉')


    args = parser.parse_args()
    tb_name = args.tieba_name
    brow = browser.AdminBrowser(args.BDUSS_key)


    if args.block:
        for _str in args.block:
            user = browser.UserInfo()
            if _str.startswith('tb.'):
                user.portrait = _str
            else:
                user.user_name = _str
            brow.block(user,tb_name,day=10)


    if args.unblock:
        brow.unblock_users(tb_name,args.unblock)


    if args.recover:
        if len(args.recover) == 1:
            brow.recover(tb_name,args.recover[0])
        elif len(args.recover) == 2:
            brow.recover(tb_name,args.recover[0],args.recover[1])
        else:
            browser.log.error('Wrong format of args --recover')


    if args.blacklist_add:
        for _str in args.blacklist_add:
            brow.blacklist_add(tb_name,_str)


    if args.blacklist_cancel:
        brow.blacklist_cancels(tb_name,args.blacklist_cancel)


    if args.good_add:
        if len(args.good_add) == 1:
            brow.good_add(tb_name,args.good_add[0])
        elif len(args.good_add) == 2:
            brow.good_add(tb_name,args.good_add[0],args.good_add[1])
        else:
            browser.log.error('Wrong format of args --good_add')


    if args.recommand:
        for tid in args.recommand:
            brow.recommend(tb_name,tid)


    if args.refuse_appeals:
        brow.refuse_appeals(tb_name)


    brow.quit()