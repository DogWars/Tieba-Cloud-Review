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
    parser.add_argument('--admin_type','-at',
                        type=str,
                        default=1,
                        help='max blocking days of the admin account')
    parser.add_argument('--block_ctrl_filepath','-bc',
                        type=str,
                        default=PATH + '/user_control/' + browser.SHOTNAME + '.json',
                        help='path of the block control json | default value for example.py is ./user_control/example.json')
    parser.add_argument('--header_filepath','-hp',
                        type=str,
                        default=PATH + '/user_control/headers.txt',
                        help='path of the headers txt | default value is ./user_control/headers.txt')
    kwargs = vars(parser.parse_args())

    try:
        with open(kwargs['block_ctrl_filepath'],'r',encoding='utf-8-sig') as block_ctrl_file:
            block_list = json.loads(block_ctrl_file.read())
    except FileExistsError:
        raise(FileExistsError('block control json not exist! Please create it!'))
    except AttributeError:
        raise(AttributeError('Incorrect format of block_control.json!'))

    try:
        admin_type = kwargs['admin_type']
    except AttributeError:
        browser.log.warning('Please input the admin_type!')
        admin_type = 1

    block_id = browser.AdminBrowser(kwargs['header_filepath'],admin_type)

    for i,block in enumerate(block_list):
        user = browser.UserInfo()
        user.user_name = block.get('user_name','')
        user.nick_name = block.get('nick_name','')
        user.portrait = block.get('portrait','')

        if user.user_name or user.nick_name or user.portrait:
            flag,user = block_id.block(user,block['tb_name'],block['day'])

        block['user_name'] = user.user_name
        block['nick_name'] = user.nick_name
        block['portrait'] = user.portrait
        block_list[i] = block

    with open(kwargs['block_ctrl_filepath'],'w',encoding='utf-8-sig') as block_ctrl_file:
        json_str = json.dumps(block_list,ensure_ascii=False,indent=2,separators=(',',':'))
        block_ctrl_file.write(json_str)

    block_id.quit()