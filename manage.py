#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-21 23:17:20
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


import os

# 开启覆盖测试
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    # 启动覆盖测试引擎, branch=True开启分支覆盖分析, include限制分析范围
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

from app import create_app, db
from app.models import User, Follow, Role, Permission, Post, Comment

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
# 导入的db开始为空对象, 上面create_app初始化完成
migrate = Migrate(app, db)


# 下列都用在(python xx.py ____)这里
# 注册app, db, User, Role
def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment)


# shell 注册make_context回调函数, 自动导入app等对象
manager.add_command('shell', Shell(make_context=make_shell_context))
# 添加一个db命令
manager.add_command('db', MigrateCommand)


# 修饰器 自定义命令, 函数名即为命令名
@manager.command
# test() 添加布尔值参数 即可 为test命令添加布尔值选项
def test(coverage=False):
    # 下列说明会在shell帮助中显示
    """Run the unit tests."""
    # 覆盖测试部分
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        # 设置环境变量
        os.environ['FLASK_COVERAGE'] = '1'
        # TODO: execvp参数含义
        # 此时全局域代码都已执行, 需要重启脚本
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    # 原单元测试
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    # 覆盖测试后续
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """ 代码分析器监视下启动 app """
    # 使用`python manage.py profile`启动, 终端会显示每条请求的分析数据
    # 包含最慢运行的25个函数, --length 选项可修改, 指定--profile_dir可用指定保存目录
    # 官方文档(https://docs.python.org/3/library/profile.html)
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """ 部署命令 """
    # 自动执行命令
    from flask_migrate import upgrade
    from app.models import Role, User

    # 迁移数据库到最新版本
    upgrade()

    Role.insert_roles()

    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
