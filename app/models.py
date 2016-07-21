#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-21 23:24:27
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon

# 用于计算用户邮箱的哈希值
import hashlib
from datetime import datetime

# 使用Werkzeug中security模块实现 密码散列
from werkzeug.security import generate_password_hash, check_password_hash
# 令牌
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
# 用于登陆
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin

from . import db, login_manager
from .exceptions import ValidationError


class Permission:
    """ 权限常量 """
    FOLLOW = 0x01  # 关注其他用户
    COMMENT = 0x02  # 在他人撰写的文章中发布评论
    WRITE_ARTICLES = 0x04  # 写文章
    MODERATE_COMMENTS = 0x08  # 查处他人的不当评论
    ADMINISTER = 0x80  # 管理网站


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 创建用户默认属于哪个角色, 该角色此处为True,
    # 只有一个角色的default字段需要设为True
    default = db.Column(db.Boolean, default=False, index=True)
    # 权限, 用一个整型, 表示位标志, '0b 0000 0000'
    permissions = db.Column(db.Integer)
    # 定义User外键的面向对象视角, 即引用模型, 而非id值
    # users返回用户组成的实例列表
    # 'User' 另一个模型名称
    # backref, 向User中添加role属性(返回实例对象), 可替代role_id(返回值)访问Role实例模型
    # lazy, 加载相关记录, dynamic, 不加载记录, 但提供加载记录的查询
    users = db.relationship('User', backref='role', lazy='dynamic')

    # 静态方法, 类方法, 与实例无关, built-in函数, 不默认传入self
    @staticmethod
    def insert_roles():
        roles = {
            # 位或操作
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        # 查询角色是否存在, 不存在则创建, 即更新操作
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            # roles字典中key=r, value是个tuple, tuple中第一个, 即位或值
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    """ 关注关联表 """
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# 继承UserMixin, 里面包含了is_authenticated等的默认实现
class User(UserMixin, db.Model):
    """ 用户表 """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # 外键, roles表id列
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    # 是否邮件激活
    confirmed = db.Column(db.Boolean, default=False)
    # 姓名
    name = db.Column(db.String(64))
    # 所在地
    location = db.Column(db.String(64))
    # 自我介绍
    # db.Text()与db.String()区别为前者不需要指定长度
    about_me = db.Column(db.Text())
    # 注册日期
    # default参数可接受函数, 所以datetime.utcnow没有(), 调用时生成当时时间
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    # 最后访问日期
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    # 头像MD5值
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 被关注者list对象
    followed = db.relationship('Follow',
                               # 指定外键 消除歧义
                               foreign_keys=[Follow.follower_id],
                               # 向Follow反向添加关注者
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               # 配置父对象上执行操作对相关对象的影响
                               # delete-orphan 删除user时同时删除联接
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    # 一的一侧定义relationship
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        """
        随机生成测试用户数据
        $ python3 manage.py shell
        >>> User.generate_fake()
        """
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def add_self_follows():
        """ 用户自关注 """
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # 若基类未定义角色
        if self.role is None:
            # 根据邮箱自动设为管理员
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            # 否则设为默认角色(由角色default属性决定)
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        # 计算邮箱md5值
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        # 设定自己关注自己, 以使首页关注的人动态中可出现自己
        # self.follow(self)     # 等价以下
        # 测试follower参数不传也可以, 暂时?
        self.followed.append(Follow(followed=self))

    # 定义为属性, 由于密码已散列, 原始密码不存在, 所以当以User.password使用时返回错误
    # 定义@property后, 调用不需要加(), 即User.password() == User.password
    # 使方法可以像属性一样使用, 如User.query
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # 只写属性, 设置密码
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """ 校验密码的hash, 返回True即密码正确 """
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        """ 注册 生成token, 默认有效1h """
        # 创建序列化器
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # 用当然用户ID生成token
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        """ 注册 确认 """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            # 还原数据
            data = s.loads(token)
        except:
            return False
        # 检查ID是否已存在db中, token被破, 也无法确认他人账户
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        """ 重置密码 生成token """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        """ 重置密码 设置新密码 """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        """ 生成更换邮箱的token """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        """ 更换邮箱 """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        """ 用户角色权限与 Permission.xx 验证 """
        # 位与操作
        return self.role is not None and (self.role.permissions &
                                          permissions) == permissions

    # 检查管理员权限功能常用, 单独实现
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        """ 更新用户最后访问时间 """
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def follow(self, user):
        """ 关注功能 """
        if not self.is_following(user):
            # 创建关注对象
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        """ 取消关注功能 """
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        """ 是否关注了某人 """
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        """ 是否被某人关注 """
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    # @property 调用类似属性, 不加(), 与其他关系的句法保持一致
    @property
    def followed_posts(self):
        """ 被关注者的所有文章 """
        # Post.query 查询主体
        #                 join 联接表      用来联接的列
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)

    def to_json(self):
        """ API 生成用户序列化字典, 为JSON化 """
        json_user = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'post': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts',
                                      id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user

    def generate_auth_token(self, expiration):
        """ 生成API认证令牌 """
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        # 默认不转码为二进制数据, 但二进制在发送的邮件中会转成ascii码
        return s.dumps({'id': self.id}).decode('ascii')

    # 解码令牌后才知道用户是谁, 所以使用静态方法
    @staticmethod
    def verify_auth_token(token):
        """ 验证API认证令牌 """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @property
    def __repr__(self):
        return '<User %r>' % self.username


# 一致性考虑, 实现匿名用户的验证方法
# noinspection PyUnusedLocal
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 匿名用户设为未登录时current_user的值
login_manager.anonymous_user = AnonymousUser


# 加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    """ 文章类 """
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    # noinspection PyUnusedLocal
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        # linkify 将纯文本中的URL转换成适当的<a>
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags,
            strip=True))

    def to_json(self):
        """ 文章的序列化字典, 为了转换成JSON"""
        json_post = {
            # 定义external, 生成站外使用的网站URL
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            # 需要返回资源的URL, 因此使用url_for
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
            'comments': url_for('api.get_post_comments', id=self.id,
                                _external=True),
            # 评论数量并不是模型的属性, 不必一对一, 只是为了方便客户端使用
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            # 因为form_json没有掌握处理问题的足够信息, 抛出异常交给调用者处理
            raise ValidationError('post does not have a body')
        return Post(body=body)


# on_changed_body函数注册在body字段上, 是SQLAlchemy 'set' 事件的监听程序
# 当类实例的body字段设了新值, 函数会自动调用 ?暂未体会到
db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    """ 评论类 """
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 多的一侧定义外键
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    # noinspection PyUnusedLocal
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        """ 评论修改触发body渲染body_html """
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        # linkify 将纯文本中的URL转换成适当的<a>
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags,
            strip=True))

    def to_json(self):
        """ API 评论 序列化字典, 转JSON用 """
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True)
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        """ API JSON格式评论创建评论类 """
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)
