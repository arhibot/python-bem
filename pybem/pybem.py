from __future__ import with_statement

import os
from glob import glob
from pprint import pformat
from itertools import chain

import PyV8
import subprocess

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
                 cache_context=False,
                 auto_rebuild=False):
        self.rootpath = rootpath
        self.techs = js_load or DEFAULT_JS_LOAD

        self.use_exts = use_exts
        self.pageextensions = {}

        self.cache_context = cache_context
        self.contexts = {}

        self.auto_rebuild = auto_rebuild

        self.toplevelcls = toplevelcls

    def rebuild(self, path):
        if path.endswith('.priv.js'):
            relname = os.path.relpath(path, self.rootpath)
            subprocess.call(['./node_modules/.bin/bem', 'make', relname], cwd=self.rootpath)
            print 'end rebuild ' + relname

    def load_pagejs_data(self, pagedir, extra_files):
        jsdata = []
        abspagedir = os.path.join(self.rootpath,
                                  pagedir)
        for tech in chain(extra_files, self.techs):
            for fname in glob(os.path.join(abspagedir, tech)):
                path = os.path.join(abspagedir,
                                    fname)
                try:
                    if self.auto_rebuild:
                        self.rebuild(path)
                    jsdata.append(open(path).read())
                except IOError:
                    pass
        return '\n'.join(jsdata).decode('utf-8')

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
            # represent Unicode symbols with JavaScript character escape sequences
            # as workaround for PyV8 issue http://code.google.com/p/pyv8/issues/detail?id=152
            page_js = js_escape_unicode(page_js)
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

        return context, prepare


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
                if return_bemjson:
                    return ctx.eval('JSON.stringify(%s(context, env))' % entrypoint)
                return ctx.eval('BEMHTML.apply(%s(context, env))' % entrypoint)
            else:
                ctx.locals.bemjson = context
                if return_bemjson:
                    return ctx.eval('JSON.stringify(bemjson)')
                return ctx.eval('BEMHTML.apply(bemjson)')


import re

ESCAPABLE = re.compile(r'([^\x00-\x7f])')
HAS_UTF8 = re.compile(r'[\x80-\xff]')


def _js_escape_unicode_re_callack(match):
    s = match.group(0)
    n = ord(s)
    if n < 0x10000:
        return r'\u%04x' % (n,)
    else:
        # surrogate pair
        n -= 0x10000
        s1 = 0xd800 | ((n >> 10) & 0x3ff)
        s2 = 0xdc00 | (n & 0x3ff)
        return r'\u%04x\u%04x' % (s1, s2)

def js_escape_unicode(s):
    """Return an ASCII-only representation of a JavaScript string"""
    if isinstance(s, str):
        if HAS_UTF8.search(s) is None:
            return s
        s = s.decode('utf-8')
    return str(ESCAPABLE.sub(_js_escape_unicode_re_callack, s))
