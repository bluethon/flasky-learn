#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-17 14:09:52
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon

import os


# 当前文件的目录(文件夹名称)的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))


# 基类, 包含通用配置
class Config:
    # 防止CSRF, wtf使用的密匙
    SECRET_KEY = os.environ.get(
        'SECRET_KEY', default=None) or 'hard to guess string'
    # SSL开关
    SSL_DISABLE = False
    # True, 每次请求结束, 自动提交数据库中变动
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 记录查询统计数字功能
    # 默认get_debug_queries仅调试可用, 为记录数据库缓慢语句, 打开
    SQLALCHEMY_RECORD_QUERIES = True
    # 邮件标题前缀
    FLASKY_MAIL_SUBJECT_PREFIX = '[FLASKY]'
    # 发送者
    FLASKY_MAIL_SENDER = 'Flasky Admin <j5088794@163.com>'
    # 管理员, 接收者
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN', default='j5088794@163.com')
    FLASKY_POSTS_PER_PAGE = 10
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 10
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    # 如果设置成True，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存
    # 2.1中默认None, 未来默认False
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 基类为空
    # 配置类可以实例化, 执行对当前环境变量的配置初始化
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', default=None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', default=None)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or (
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite'))


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or (
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))
    # 关闭CSRF保护功能, 方便测试
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        'sqlite:///' + os.path.join(basedir, 'data.sqlite'))

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 错误信息 邮件通知管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None) and \
                    getattr(cls, 'MAIL_USE_SSL', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        # 邮件日志纪录全等级为ERROR, 只有错误日志才会发送邮件
        mail_handler.setLevel(logging.ERROR)
        # 配置程序的日志记录器将错误写入邮件日志记录器
        app.logger.addHandler(mail_handler)


class HerokuConfig(Config):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        """
        加入Werkzeug提供的WSGI中间件
        检查代理服务器发出的自定义首部并对请求对象进行更新
        使用Heroku, 会在客户端和app间加入反代, 反代到app由于在Heroku内部使用SSL
        Eg: 修改后request.is_secure使用Client -> Reverse Proxy的请安全性
        处理代理服务器首部
        handle proxy server headers
        """
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # Heroku中, 日志写入stdout或stderr, Heroku才会捕获到
        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


# config字典注册不同的配置环境
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,

    'default': DevelopmentConfig
}
