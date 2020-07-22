#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import argparse

import re
import browser

PATH = os.path.split(os.path.realpath(sys.argv[0]))[0].replace('\\','/')


parser = argparse.ArgumentParser(description='TEST')
parser.add_argument('--header_filepath', '-hp',type=str,default=PATH + '/user_control/headers.txt', help='path of the headers txt')
kwargs = vars(parser.parse_args())

brow = browser.Browser(kwargs['header_filepath'])

threads = brow._app_get_threads('vtuber',rn=5)
for thread in threads:
    print(thread.title)

brow.quit()