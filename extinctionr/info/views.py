from hashlib import md5
from django.views.generic import TemplateView, ListView, DetailView
from django.http import Http404
from django.utils.decorators import method_decorator
from django.template.loader import get_template, TemplateDoesNotExist
from django.views.decorators.http import etag

from .models import PressRelease



def get_template_etag(request, *args, **kwargs):
    page = kwargs['page']
    if page.endswith('.html'):
        page = page.split('.')[0]
    try:
        template_name = 'pages/%s.html' % page
        template = get_template(template_name).template
        request.template_name = template_name
        if not request.user.is_authenticated:
            return md5(template.source.encode('utf8')).hexdigest()
    except TemplateDoesNotExist:
        raise Http404(page)


class InfoView(TemplateView):
    @method_decorator(etag(get_template_etag))
    def get(self, request, *args, **kwargs):
        self.template_name = request.template_name
        response = super(InfoView, self).get(request, *args, **kwargs)
        return response


class PRListView(ListView):
    def get_queryset(self):
        return PressRelease.objects.released()


class PRDetailView(DetailView):
    def get_queryset(self):
        return PressRelease.objects.released()
