import os
from glob import glob

import PyV8

RETURN_BEMJSON = 'RETURN_BEMJSON'

DEFAULT_JS_LOAD = ['*.bemhtml.js', '*.priv.js']
JS_EXTENSION_NAME = 'bem/%(pagedir)s'

BEMHTML_RENDER = 'BEMHTML.apply(%s)'


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
                    jsdata.append(open(path).read())
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


    def get_pyv8_context(self, pagedir, use_exts):
        exts = []
        prepare = ''
        if use_exts:
            name, _exts_objs = self.get_extensions(pagedir)
            exts = [name]
        else:
            prepare = self.load_pagejs_data(pagedir)
        return PyV8.JSContext(extensions=exts), prepare.decode('utf8')


    def render(self, pagedir, context, env, entrypoint, use_exts=False, return_bemjson=False):
        '''
        create bemjson and render it

        context: python object
        env: python object
        entrypoint: name of js function

        BEMHTML.apply(entrypoint(context, env))
        '''

        ctx, prepare = self.get_pyv8_context(pagedir, use_exts)
        with ctx:
            if prepare:
                ctx.eval(prepare)
            ctx.locals.context = context
            ctx.locals.env = env
            if entrypoint:
                ctx.locals.bemjson = ctx.eval('%s(context, env)' % entrypoint)
            else:
                ctx.locals.bemjson = context
            if return_bemjson:
                return ctx.eval('JSON.stringify(bemjson)')
            return ctx.eval('BEMHTML.apply(bemjson)')
