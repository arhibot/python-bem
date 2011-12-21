import os
from glob import glob

import PyV8

from .import utils


DEFAULT_JS_LOAD = ['*.bemhtml.js', '*.priv.js']
JS_EXTENSION_NAME = 'bem/%(pagedir)s'


class BEMRender(object):
    def __init__(self, rootpath, js_load=None):
        self.rootpath = rootpath
        self.contexts = {}
        self.techs = js_load or DEFAULT_JS_LOAD
        self.pageextensions = {}


    def load_pagejs_data(self, pagedir):
        jsdata = []
        abspagedir = os.path.join(self.rootpath,
                                  pagedir)
        for tech in self.techs:
            for fname in glob(os.path.join(abspagedir, tech)):
                path = os.path.join(abspagedir,
                                    fname)
                try:
                    jsdata.append(utils.smart_str(open(path).read()))
                except IOError, e:
                    print e
        return '\n'.join(jsdata)


    def get_extensions(self, pagedir):
        '''
        pagedir: 'pages-touch/index'
        '''
        exts = self.pageextensions.get(pagedir)
        name = JS_EXTENSION_NAME % {'pagedir': pagedir}
        if exts is None:
            page_js = self.load_pagejs_data(pagedir)
            exts = [PyV8.JSExtension(name, page_js)]
            self.pageextensions[pagedir] = exts
        return name, exts


    def get_pyv8_context(self, pagedir):
        name, _exts = self.get_extensions(pagedir)
        return PyV8.JSContext(extensions=[name])


    def render(self, pagedir, context, env, entrypoint):
        '''
        create bemjson and render it
        
        context: python object
        env: python object
        entrypoint: name of js function

        BEMHTML.apply(entrypoint(context, env))
        '''
        with self.get_pyv8_context(pagedir) as ctx:
            block = ctx.eval(entrypoint)
            bemjson = block(context, env)
            bem = ctx.eval('BEMHTML')
            return bem.apply(bemjson)
