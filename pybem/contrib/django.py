from django import http
from django.core.urlresolvers import reverse
from django.utils import translation
from django.conf import settings

from pybem import pybem

__all__ = ['BEMResponseMixin']


class BEMResponseMixin(object):
    '''
    A mixin that can be used to render a template.

    Should be used in an interchangeable manner with
        `django.views.generic.TemplateResponseMixin`.
    '''
    template_name = None
    entrypoint = 'render'
    renderer_cls = pybem.BEMRender
    rootpath = None

    def get_renderer_cls(self):
        return self.renderer_cls

    def get_rootpath(self):
        if self.rootpath:
            return self.rootpath
        else:
            rootpath = getattr(settings, 'FRONTEND_ROOT', None)
            if not rootpath:
                raise ValueError('rootpath is not specified')
            return rootpath

    def get_renderer_kwargs(self):
        return {}

    def get_renderer(self):
        '''
        Return a BEMRender instance.
        '''

        cls = self.get_renderer_cls()
        rootpath = self.get_renderer_rootpath()
        kwargs = self.get_renderer_kwargs()

        return cls(rootpath, **kwargs)

    def get_bem_env(self, context):
        '''
        Return an environment to be passed in BEM entry point.
        '''
        return  {
            'request': self.request,
            'settings': settings,
            'gettext': translation.gettext,
            'ngettext': translation.ngettext,
            'url':
                lambda name, args=None, kwargs=None:
                    reverse(name, args=args, kwargs=kwargs),
        }

    def render_to_response(self, context, extra_files=None, **response_kwargs):
        '''
        Returns a response with a template rendered with the given context.
        '''
        env = self.get_bem_env(context)

        content = self.renderer.render(
            self.get_template_name(),
            context, env, self.entrypoint,
            extra_files=extra_files)

        return http.HttpResponse(content, **response_kwargs)

    def get_template_name(self):
        '''
        Returns a template name to be used for the request. Must return
        a string. May not be called if render_to_response is overridden.
        '''
        if self.template_name is not None:
            return self.template_name
        else:
            raise ValueError('template_name is not specified')
