#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-04 17:39
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon


from flask import jsonify

from app.exceptions import ValidationError
from . import api


def bad_request(message):
    """ 自定义400错误 """
    # Flask的jsonify可用Python的dic生成JSON响应
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    """ 自定义401错误 """
    # Flask-HTTPAuth默认自动生成401状态码, 但为了API一致性, 因此自定义了错误响应
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    """ 自定义403错误 """
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


# errorhandler修饰器接收Exception类参数, 抛出ValidationError, 调用被修饰函数
# 修饰器从API蓝本中调用, 只有处理蓝本路由时抛出异常才会调用
# 此处使用的errorhandler与main.error中为同一个
@api.errorhandler(ValidationError)
def validation_error(e):
    """ 捕获ValidationError, 返回400错误 """
    return bad_request(e.args[0])
