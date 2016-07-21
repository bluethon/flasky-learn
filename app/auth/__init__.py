#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-25 23:12:05
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from flask import Blueprint


auth = Blueprint('auth', __name__)

# noinspection PyUnresolvedReferences
from . import views
