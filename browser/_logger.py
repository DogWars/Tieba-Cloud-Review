# -*- coding:utf-8 -*-
__all__ = ('SCRIPT_PATH','FILENAME','SHOTNAME',
           'MyLogger')



import os
import sys
import time

import logging



PATH = os.path.split(os.path.realpath(__file__))[0]
SCRIPT_PATH,FILENAME = os.path.split(os.path.realpath(sys.argv[0]))
SHOTNAME = os.path.splitext(FILENAME)[0]



class MyLogger(logging.Logger):
    """
    MyLogger(name=__name__)

    自定义的日志记录类
    """


    def __init__(self,name = __name__):

        super(MyLogger,self).__init__(__name__)

        if not os.path.exists(PATH + '/log'):
            os.mkdir(PATH + '/log')
        recent_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        log_filepath = os.path.join(PATH,'log',''.join([SHOTNAME.upper(),'_',recent_time,'.log']))
        try:
            file_handler = logging.FileHandler(log_filepath,encoding='utf-8')
        except (PermissionError):
            try:
                os.remove(log_filepath)
            except (OSError):
                raise(OSError('''Can't write and remove {path}'''.format(path=log_filepath)))
            else:
                file_handler = logging.FileHandler(log_filepath,encoding='utf-8')

        stream_handler = logging.StreamHandler(sys.stdout)

        file_handler.setLevel(logging.INFO)
        stream_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("<%(asctime)s> [%(levelname)s] %(message)s","%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        self.addHandler(file_handler)
        self.addHandler(stream_handler)
        self.setLevel(logging.DEBUG)