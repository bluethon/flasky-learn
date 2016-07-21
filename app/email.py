#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-04-23 11:46:46
# @Author  : Bluethon (j5088794@gmail.com)
# @Link    : http://github.com/bluethon


from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail


def send_async_email(app, msg):
    # 在不同的线程中执行, 因此需要手动激活app_context
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject=app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  recipients=[to], sender=app.config['FLASKY_MAIL_SENDER'])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
