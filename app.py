#!/usr/bin/env python
# coding: utf-8

import web
import sqlite3
import json
import dill

from api import PCS, CaptchaError, LoginFailed

web.config.debug = False

urls = (
    '/login', 'login',
)

app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})
render = web.template.render('templates')


class login:
    def GET(self):
        i = web.input(username=None, password=None, captcha=None)
        if not i.username or not i.password:
            return

        exception = None
        captcha_url = None
        try:
            if 'pcs' in session:
                pcs = dill.loads(session['pcs'])
                print(session['count'])
            else:
                pcs = PCS(i.username, i.password.encode('ascii'))

            if i.captcha: pcs.captcha = i.captcha
            pcs._login()
        except CaptchaError as e:
            exception = 'Need captcha'
            captcha_url = pcs.captcha_url
        except LoginFailed as e:
            exception = str(e)
        finally:
            session['pcs'] = dill.dumps(pcs)
            session.count += 1

        if exception:
            if captcha_url:
                return render.index(captcha_url)
            else:
                return exception
        else:
            return '登陆成功'

    def POST(self):
        return self.GET()




if __name__ == '__main__':
    app.run()

