#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-06 14:15
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon

from functools import wraps
from flask import g

from .errors import forbidden


def permission_required(permission):
    """ API 权限装饰器 """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
