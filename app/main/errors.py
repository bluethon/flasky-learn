#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-21 21:12:38
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from flask import render_template, request, jsonify
from . import main


# noinspection PyUnusedLocal
@main.app_errorhandler(403)
def forbidden(e):
    # Werkzeug将Accept请求首部解码为request.accept_mimetypes
    # 根据首部的值决定客户端期望接收的响应格式
    # 浏览器一般不显示响应格式, 所以仅当客户端接受JSON不接受HTML时生成JSON格式响应
    if request.accept_mimetypes.accept_json and not \
            request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


# errorhandler只有蓝本中错误才能触发
# app_errorhandler才能注册为全局的错误处理程序
# noinspection PyUnusedLocal
@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and not \
            request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


# noinspection PyUnusedLocal
@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not \
            request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
