#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-03-22 22:26:37
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon

import os
from threading import Thread

from flask import Flask, render_template, session, redirect, url_for
from flask.ext.script import Manager, Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask.ext.sqlalchemy import SQLAlchemy


# 获取当前文件路径
basedir = os.path.abspath(os.path.dirname(__file__))

# Flask类的构造函数必填参数只有一个, 即程序主模块或包的名字
# 在大多数情况下, Python的__name__变量即为所需值
# Flask用此参数决定程序的根目录, 以便找资源文件的相对位置
app = Flask(__name__)
# 设置密匙
app.config['SECRET_KEY'] = 'hard to guess string'
# 设置数据库路径, 数据库文件名称
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + os.path.join(basedir, 'data.sqlite'))
# True, 每次请求结束, 自动提交数据库中变动
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# Mail配置
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', default=None)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', default=None)
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN', default=None)
# prefix 前缀
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <j5088794@163.com>'


# 命令行可执行启动参数
manager = Manager(app)
# 调试模式
# manager.add_command("runserver", Server(use_debugger=True))
# 用户界面插件
bootstrap = Bootstrap(app)
# 本地化时间
moment = Moment(app)
# 数据库实例
db = SQLAlchemy(app)
# 数据库迁移
migrate = Migrate(app=app, db=db, directory='migrations')
manager.add_command('db', MigrateCommand)
# 邮件
mail = Mail(app=app)


# 定义模型
class Role(db.Model):
    """docstring for Role"""
    # 定义数据库使用的表名, 若未定义, 会生成默认名称
    __tablename__ = 'roles'
    # 模型属性
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # users属性代表此关系的面向对象视角
    # 返回与角色关联的用户组列表
    # 第一个参数, 另一端是哪个模型
    # backref, 向User添加role属性, 可替代role.id访问Role, 得到的是对象, 而非外键值
    users = db.relationship('User', backref='role', lazy='dynamic')

    # 重载repr函数, 给解释器的显示类型
    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    """docstring for User"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # 外键, roles表的id列
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # 重载repr函数, 给解释器的显示类型
    def __repr__(self):
        return '<User %r>' % self.username


# 定义表单类
class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


# 为shell命令添加上下文, 注册一个make_context回调函数
# 使在shell中可以直接使用 app, db 等
def make_shell_context():
    # 注册        程序      数据库 数据库模型1  数据库模型2
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command('shell', Shell(make_context=make_shell_context))


# 异步后台线程发送邮件
def send_async_email(app, msg):
    # mail.send()使用current_app, 此处为另一线程, 需要手动激活context
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    # subject为标题内容
    msg = Message(subject=app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  recipients=[to], sender=app.config['FLASKY_MAIL_SENDER'])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    # mail.send(msg)
    # 创建线程, 发送邮件
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


# 程序实例需要知道对每个URL请求运行哪些代码, 所以保存一个URL到Python函数的映射关系
# 处理URL和函数间关系的程序称为路由
# 使用修饰器把函数注册为事件的处理程序
@app.route('/', methods=['GET', 'POST'])
# 视图函数(view function)
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            # 收件人存在
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))


# 动态路由
# 默认使用字符串
# Flask支持使用int, float, path类型
# path类型也是字符串, 只是不把斜线视作分隔符, 而是当做动态片段的一部分
# eg: /user/<int:id> 只匹配片段id为整数的URL
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# 自定义错误页面
# 404, 客户端请求未知页面或路由
@app.errorhandler(404)
def page_not_found(e):
    # 除正常返回响应外, 还返回与该错误对应的数字状态码
    return render_template('404.html'), 404


# 500, 有未处理的异常
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# 此处写法确保执行这个脚本时才启动开发服务器
if __name__ == '__main__':
    # app.run(debug=True)
    manager.run()
