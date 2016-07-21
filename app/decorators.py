#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2016-05-17 11:18:14
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


# 定义修饰器(带参数)
def permission_required(permission):
    """ 检查常规权限 """
    def decorator(f):
        # 复制原始函数f内置属性
        @wraps(f)
        # 实现修饰功能
        def decorated_function(*args, **kwargs):
            # 不具有指定权限, 返回403
            if not current_user.can(permission):
                abort(403)
            # 继续执行原函数
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 检查管理员权限
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
