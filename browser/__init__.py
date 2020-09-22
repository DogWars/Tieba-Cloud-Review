# -*- coding:utf-8 -*-
"""
@Author: Starry
@License: MIT
@Homepage: https://github.com/Starry-OvO
@Required Modules:
    sudo pip install mysql-connector
    sudo pip install lxml
    sudo pip install bs4
    sudo pip install pillow
    sudo pip install imagehash
    sudo pip install pypinyin

    可能需要的第三方yum源: Raven(https://centos.pkgs.org/8/raven-x86_64/raven-release-1.0-1.el8.noarch.rpm.html)
    使用 [rpm -Uvh xxx.rpm] 来安装Raven源
    用 [sudo yum install zbar-devel] 来安装zbar支持
    用 [sudo pip install pyzbar] 来安装pyzbar
"""

from .__define__ import *
from ._browser import *
from .admin_browser import *
from .cloud_review import *