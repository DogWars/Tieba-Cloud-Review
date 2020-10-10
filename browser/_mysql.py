# -*- coding:utf-8 -*-
import os

import json

import mysql.connector

from .__define__ import SCRIPT_PATH
from ._logger import log



class _MySQL(object):
    """
    MySQL链接基类

    _MySQL(db_name)
    """


    __slots__ = ('db_name','mydb','mycursor')


    def __init__(self,db_name):

        try:
            file = open(os.path.join(SCRIPT_PATH,'user_control/mysql.json'),'r',encoding='utf-8')
            mysql_json = json.load(file)
            file.close()
        except IOError:
            log.critical("Unable to read mysql.json!")
            raise

        self.db_name=db_name

        try:
            self.mydb = mysql.connector.connect(**mysql_json,database=db_name)
            self.mycursor = self.mydb.cursor()
        except mysql.connector.errors.ProgrammingError:
            self.mycursor.execute("CREATE DATABASE {database}".format(database=db_name))
            self.mycursor.execute("USE {database}".format(database=db_name))
        except:
            log.critical('Cannot link to the database!')
            raise


    def quit(self):
        self.mydb.commit()
        self.mydb.close()


    def ping(self):
        """
        尝试重连
        """

        try:
            self.mydb.cmd_ping()
        except:
            try:
                self.mydb.reconnect()
                self.mycursor = self.mydb.cursor()
                self.mycursor.execute("USE {database}".format(database=self.db_name))
            except:
                return False
            return True
        else:
            return True