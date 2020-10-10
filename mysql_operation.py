#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

import re
import browser

import csv



PATH = os.path.split(os.path.realpath(sys.argv[0]))[0]



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MySQL黑白名单操作',allow_abbrev=False)
    parser.add_argument('--tb_name_eng','-be',
                        type=str,
                        help='贴吧英文名',
                        required=True)
    parser.add_argument('--user_name','-u',
                        type=str,
                        help='用户名（和portrait二选一即可）')
    parser.add_argument('--portrait','-p',
                        type=str,
                        help='用户portrait')
    parser.add_argument('--white','-w',
                        action='store_true',
                        help='是否添加为白名单，默认添加为黑名单')
    parser.add_argument('--delete','-d',
                        action='store_true',
                        help='是否从名单中删除')

    parser.add_argument('--delete_new','-dn',
                        type=int,
                        help='是否删除最近n小时的pid记录',
                        metavar='HOUR')
    args = parser.parse_args()

    brow = browser.CloudReview('default','null',args.tb_name_eng)

    if args.delete_new:
        brow.mysql.del_pid(args.delete_new)

    if args.portrait or args.user_name:
        if args.delete:
            brow.del_portrait(portrait=args.portrait,user_name=args.user_name)
        else:
            brow.add_portrait(portrait=args.portrait,user_name=args.user_name,mode=args.white)

    brow.quit()
