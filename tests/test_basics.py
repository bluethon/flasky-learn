#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-23 11:59:05
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


import unittest
from flask import current_app
from app import create_app, db


class SetUp(unittest.TestCase):
    def setUp(self):
        # 使用测试配置创建程序
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        # 激活上下文, 确保能在测试中使用current_app
        # push或者with激活, pop关闭
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
