from hashlib import md5
from django.views.generic import TemplateView, ListView, DetailView
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.http import http_date
from django.template.loader import get_template, TemplateDoesNotExist
from django.views.decorators.http import etag

from .models import PressRelease


class InfoView(TemplateView):
    def get(self, request, *args, **kwargs):
        page = kwargs['page']
        if page.endswith('.html'):
            page = page.split('.')[0]
        try:
            template_name = 'pages/%s.html' % page
            get_template(template_name).template
            self.template_name = template_name
        except TemplateDoesNotExist:
            raise Http404(page)
        tresp = super(InfoView, self).get(request, *args, **kwargs)
        response = HttpResponse(tresp.rendered_content)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache'
        # response['Etag'] = md5(response.content).hexdigest()
        return response


class PRListView(ListView):
    def get_queryset(self):
        if self.request.user.has_perm('info.view_pressrelease'):
            return PressRelease.objects.all()
        else:
            return PressRelease.objects.released()


    def render_to_response(self, context, **kwargs):
        resp = super().render_to_response(context, **kwargs)
        resp['Last-Modified'] = http_date(context['object_list'].last().modified.timestamp())
        if self.request.user.is_authenticated:
            resp['Cache-Control'] = 'no-cache'
        return resp


class PRDetailView(DetailView):
    def get_queryset(self):
        if self.request.user.has_perm('info.view_pressrelease'):
            return PressRelease.objects.all()
        else:
            return PressRelease.objects.released()

    def render_to_response(self, context, **kwargs):
        resp = super().render_to_response(context, **kwargs)
        resp['Last-Modified'] = http_date(context['object'].modified.timestamp())
        if self.request.user.is_authenticated:
            resp['Cache-Control'] = 'no-cache'
        return resp
