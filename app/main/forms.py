#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-21 21:54:11
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from flask_wtf import Form
from flask_pagedown.fields import PageDownField

from wtforms import StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError

from ..models import Role, User


class NameForm(Form):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(Form):
    """ 用户使用的资料编辑表 """
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    """ 管理员使用的资料编辑表 """
    email = StringField('Email',
                        validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[DataRequired(), Length(1, 64),
                                       Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only '
                                              'letters, numbers, dots or '
                                              'underscores')])
    confirmed = BooleanField('Confirmed')
    # role.id为字符串, coerce(强迫)将值转换为整数
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        """"""
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        # 设置角色选择列表, 选项必须是元组组成的列表, 包含(标识符, 显示文本)
        # 列表按角色字母顺序排序
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, filed):
        # 如果字段未修改, 跳过验证
        if filed.data != self.user.email and User.query.filter_by(
                email=filed.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, filed):
        if filed.data != self.user.username and User.query.filter_by(
                username=filed.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    """ 文章表 """
    # 使用markdown字段类型
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(Form):
    """ 评论表 """
    body = StringField('Enter your comment', validators=[DataRequired()])
    submit = SubmitField('Submit')

