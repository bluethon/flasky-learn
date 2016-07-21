#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date     : 2016-07-19 15:44
# @Author   : Bluethon (j5088794@gmail.com)
# @Link     : http://github.com/bluethon

"""
chrome测试浏览器下载
https://sites.google.com/a/chromium.org/chromedriver/
"""

import re
import threading
import time
import unittest
from selenium import webdriver

from app import create_app, db
from app.models import Role, User, Post


class SeleniumTestCase(unittest.TestCase):
    """ Selenium测试类 """
    client = None

    @classmethod
    def setUpClass(cls):
        # start Chrome
        try:
            # 此处改为使用chrome, 写明路径, 此处相对路径为使用 test命令测试
            cls.client = webdriver.Chrome('./tmp/chromedriver')
            # 此处改为使用chrome, 写明路径, 此处相对路径为使用此文件单独测试
            # cls.client = webdriver.Chrome('../tmp/chromedriver')
        except:
            pass

        # 如果浏览器未启动, 则跳过测试
        if cls.client:
            # 创建 app
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志, 保持测试输出整洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            # 创建数据库和测试数据
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            # 添加一个管理员
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='john@example.com', username='john',
                         password='cat', role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 单独线程运行Flask服务器
            threading.Thread(target=cls.app.run).start()

            # 延迟1s, 确保服务器已启动
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭Flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            # 销毁数据库
            db.drop_all()
            db.session.remove()

            # 删除程序上下文
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        """ 测试 客户端 管理员主页 """
        # 访问首页
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,\s+Stranger\s+!',
                                  self.client.page_source))

        # 进入登录页面
        self.client.find_element_by_link_text('Log In').click()
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        # 登录
        self.client.find_element_by_name('email').send_keys('john@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,\s+john\s+!',
                                  self.client.page_source))

        # 进入用户个人资料页面
        self.client.find_element_by_link_text('Profile').click()
        self.assertTrue('<h1>john</h1>' in self.client.page_source)
