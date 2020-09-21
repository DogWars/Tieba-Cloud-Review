#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import argparse

import json
import browser



PATH = os.path.split(os.path.realpath(__file__))[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Block Tieba ID')
    parser.add_argument('--block_ctrl_filepath','-bc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='block_control.json的路径，对example.py而言默认值为./user_control/example.json')
    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='headers.txt（包含BDUSS的消息头）的路径，默认值为./user_control/headers.txt')
    args = parser.parse_args()

    try:
        with open(args.block_ctrl_filepath,'r',encoding='utf-8-sig') as block_ctrl_file:
            block_list = json.loads(block_ctrl_file.read())
    except FileExistsError:
        raise(FileExistsError('block control json not exist! Please create it!'))
    except AttributeError:
        raise(AttributeError('Incorrect format of block_control.json!'))

    block_id = browser.AdminBrowser(args.header_filepath)

    for i,block in enumerate(block_list):
        user = browser.UserInfo()
        user.user_name = block.get('user_name','')
        user.nick_name = block.get('nick_name','')
        user.portrait = block.get('portrait','')

        flag = True
        if user.user_name or user.nick_name or user.portrait:
            flag,user = block_id.block(user,block['tb_name'],block['day'])

        block['user_name'] = user.user_name
        block['nick_name'] = user.nick_name
        block['portrait'] = user.portrait
        if not flag:
            block['reason'] = 'ERROR'

        block_list[i] = block

    with open(args.block_ctrl_filepath,'w',encoding='utf-8-sig') as block_ctrl_file:
        json_str = json.dumps(block_list,ensure_ascii=False,indent=2,separators=(',',':'))
        block_ctrl_file.write(json_str)

    block_id.quit()