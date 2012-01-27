#-*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

import tornado.ioloop
import tornado.web

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '../'))
from pybem import pybem


# Path with pages dirs
wwwpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'www')
# Create BEM renderer
renderer = pybem.BEMRender(wwwpath)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # Create some dynamic context
        context = {'url' : 'http://example.com/',
                   'text': 'Привет',
                   'title': lambda title: '(%s) %s' % (self.request.uri, title)}# (path. request.uri)}
        env = self.request
        # Render page example from pages
        # Calls BEMHTML.apply(render(context, env))
        message = renderer.render('pages/example', context, env, "render", False)
        self.write(message)

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(wwwpath, 'pages')}),
        (r"/blocks/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(wwwpath, 'blocks')}),
        (r"/bem-bl/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(wwwpath, 'bem-bl')}),
    ])
    application.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
