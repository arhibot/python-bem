from __future__ import with_statement

import os
from glob import glob
from pprint import pformat
from itertools import chain

import PyV8

DEFAULT_JS_LOAD = ['*.bemhtml.js', '*.priv.js']
JS_EXTENSION_NAME = 'bem/%(pagedir)s/_extra_:%(suffix)s'

BEMHTML_RENDER = 'BEMHTML.apply(%s)'


class TopLevelUtils(PyV8.JSClass):
    def pprint(self, value, to_term=True):
        s = pformat(value)
        if to_term:
            print s
        return s


class BEMRender(object):
    def __init__(self,
                 rootpath,
                 js_load=None,
                 toplevelcls=TopLevelUtils,
                 use_exts=False,
                 cache_context=False):
        self.rootpath = rootpath
        self.techs = js_load or DEFAULT_JS_LOAD

        self.use_exts = use_exts
        self.pageextensions = {}

        self.cache_context = cache_context
        self.contexts = {}

        self.toplevelcls = toplevelcls


    def load_pagejs_data(self, pagedir, extra_files):
        jsdata = []
        abspagedir = os.path.join(self.rootpath,
                                  pagedir)
        for tech in chain(extra_files, self.techs):
            for fname in glob(os.path.join(abspagedir, tech)):
                path = os.path.join(abspagedir,
                                    fname)
                try:
                    jsdata.append(open(path).read())
                except IOError:
                    pass
        return '\n'.join(jsdata)


    def get_extensions(self, pagedir, extra_files):
        '''
        pagedir: 'pages-touch/index'
        '''
        suffix = '/'.join(extra_files)
        name = JS_EXTENSION_NAME % {'pagedir': pagedir,
                                    'suffix': suffix}
        ext = self.pageextensions.get(name)

        if ext is None:
            page_js = self.load_pagejs_data(pagedir, extra_files)
            ext = PyV8.JSExtension(name, page_js)
            self.pageextensions[name] = ext
        return name, ext


    def get_pyv8_context(self, pagedir, extra_files):
        if self.cache_context:
            context_name = pagedir + '/'.join(extra_files)
            context = self.contexts.get(context_name)
            if context:
                return context, ''

        exts = []
        prepare = ''
        if self.use_exts:
            name, _exts_objs = self.get_extensions(pagedir, extra_files)
            exts = [name]
        else:
            prepare = self.load_pagejs_data(pagedir, extra_files)
        context = PyV8.JSContext(self.toplevelcls(),
                                 extensions=exts)

        if self.cache_context:
            self.contexts[context_name] = context

        return context, prepare.decode('utf8')


    def render(self, pagedir, context, env, entrypoint,
               return_bemjson=False,
               extra_files=None):
        '''
        create bemjson and render it

        context: python object
        env: python object
        entrypoint: name of js function

        BEMHTML.apply(entrypoint(context, env))
        '''

        ctx, prepare = self.get_pyv8_context(pagedir, extra_files or [])
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
