#!/usr/bin/env python
# coding: utf-8

import web
import sqlite3
import json
import dill

from api import PCS, CaptchaError, LoginFailed

web.config.debug = False

urls = (
    '/cookielogin', 'CookieLogin',
    '/profile', 'Profile'
)

app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0, 'login': False})
render = web.template.render('templates')


class CookieLogin:
    def GET(self):
        return render.login()

    def POST(self):
        i = web.input(cookie=None)
        if not i.cookie:
            raise web.SeeOther('/cookielogin')

        cookie_list = i.cookie.split(';')
        pcs = PCS('0', '0')
        pcs.session.cookies.clear()
        for c in cookie_list:
            if not c: continue
            k, v = c.split('=', 1)
            pcs.session.cookies[k] = v

        pcs.user['BDUSS'] = pcs.session.cookies['BDUSS']
        session.pcs = dill.dumps(pcs)
        session.login = True

        raise web.SeeOther('/profile')


class Profile:
    def GET(self):
        if session.login is not True:
            raise web.SeeOther('/cookielogin')

        pcs = dill.loads(session.pcs)
        assert isinstance(pcs, PCS)
        return pcs.list_files('/').content


class UserPassLogin:
    def GET(self):
        i = web.input(username=None, password=None, captcha=None)
        if not i.username or not i.password:
            return

        exception = None
        captcha_url = None
        if 'pcs' in session:
            pcs = dill.loads(session['pcs'])
            first_login = False
        else:
            pcs = PCS(i.username, i.password.encode('ascii'))
            first_login = True

        pcs.relogin_info['captcha'] = i.captcha

        return pcs.list_files('/').content

        try:
            pcs._login(first_login)
        except CaptchaError as e:
            exception = 'Need captcha'
            captcha_url = pcs.relogin_info['captcha_url']
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
    web.runwsgi()
    web.loadhook()
    import web.httpserver
    web.httpserver.WSGIServer()
    app.run()

