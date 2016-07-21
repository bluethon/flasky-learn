#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-04 17:39
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon


from flask import Blueprint

api = Blueprint('api', __name__)

# noinspection PyUnresolvedReferences
from . import authentication, posts, users, comments, errors
