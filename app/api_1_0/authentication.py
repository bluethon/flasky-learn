#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-04 17:39
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon


from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

# 此扩展只在API蓝本中使用, 因此在此处初始化, 而不是app中
# HTTP认证协议库, 细节隐藏在修饰器中
# **注意** 此处auth和auth蓝本不是一个意思
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """ API 验证认证程序 """
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    # 密码为空, 假定令牌认证
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        # 为了方视图函数能区分是令牌认证还是普通邮件验证
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    # 此验证回调函数把通过认证的用户保存在全局对象g中来允许访问视图函数
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """ 认证密令不正确, 返回401错误 """
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    """ 访问前全局验证 """
    # 附加认证, 拒绝通过认证但是没有确认账户的用户
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/token')
def get_token():
    """ API 生成JSON格式认证令牌 """
    # 验证token_used, 防止客户端使用旧令牌申请新令牌
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
