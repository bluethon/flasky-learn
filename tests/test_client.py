#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-14 15:27
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon


import re
import unittest

from flask import url_for

from app import create_app, db
from app.models import User, Role


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        # Flask测试客户端对象, 启用use_cookies选项
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        # get()得到的是Flask的Response对象, 内容是视图函数的响应
        response = self.client.get(url_for('main1.index'))
        self.assertTrue(b'Stranger' in response.data)

    def test_register_and_login(self):
        """ 注册新用户 """
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat',
        })
        self.assertTrue(response.status_code == 302)

        # 登陆
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
        }, follow_redirects=True)
        # follow_redirects设置后, 返回的不是302状态码, 是unconfirmed.html
        # 使用re是防止动态+静态拼接出现的额外空白干扰
        self.assertTrue(re.search(b'Hello,\s+john!', response.data))
        self.assertTrue(b'You have not confirmed your account yet' in
                        response.data)

        # 激活邮箱
        user = User.query.filter_by(email='john@example.com').first()
        # 忽略了注册时的令牌, 重新生成令牌
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue(b'You have confirmed your account' in response.data)

        # 注销登陆
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue(b'You have been logged out' in response.data)
