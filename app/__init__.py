#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-18 20:46:58
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown


from config import config


# 初始化__init__内也是调用init_app()
# 此处先生成空对象
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()       # markdown支持

login_manager = LoginManager()
login_manager.session_protection = 'strong'
# 设置登陆页面的端点           蓝本名称.路由
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # init_app为空, 暂时没用
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # 生产环境启动https
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # 导入蓝本, 开始定义路由, 因为否则无法使用app.route等修饰器
    from .main import main as main_blueprint
    # 蓝本中定义的路由处于休眠状态, 直到蓝本注册到app上后, 路由才真正成为app的一部分
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    # 可选参数 url_prefix
    # 注册后蓝本中定义的所有路由都会加上指定前缀, 即 '/auth'
    # eg. /login 注册位 /auth/login, 完整URL->http://localhost:5000/auth/login
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # API蓝本
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    # 附加路由和自定义的错误页面
    # 已被分解到main中

    return app
