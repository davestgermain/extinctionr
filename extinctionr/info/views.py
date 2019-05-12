from hashlib import md5

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404, HttpResponse
from django.template.loader import TemplateDoesNotExist, get_template
from django.utils.decorators import method_decorator
from django.utils.http import http_date
from django.views.decorators.http import etag
from django.views.decorators.cache import cache_page
from django.views.generic import FormView, DetailView, ListView, TemplateView

from .models import PressRelease


class RegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("email",)
        field_classes = {'email': forms.EmailField}


class RegistrationView(FormView):
    form_class = RegistrationForm
    success_url = '/'
    template_name = 'registration/register.html'

    def form_valid(self, form):
        self.object = form.save()
        self.object.username = self.object.email
        self.object.save()
        login(self.request, self.object)
        return super().form_valid(form)


@method_decorator(cache_page(1200), name='dispatch')
class InfoView(TemplateView):
    def get(self, request, *args, **kwargs):
        page = kwargs['page']
        if page.endswith('.html'):
            page = page.split('.')[0]
        elif page.endswith('/'):
            page += 'index'
        try:
            template_name = 'pages/%s.html' % page
            get_template(template_name).template
            self.template_name = template_name
        except TemplateDoesNotExist:
            raise Http404(page)
        tresp = super(InfoView, self).get(request, *args, **kwargs)
        response = HttpResponse(tresp.rendered_content)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


@method_decorator(cache_page(1200), name='dispatch')
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
            resp['Cache-Control'] = 'private'
        return resp

@method_decorator(cache_page(1200), name='dispatch')
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
            resp['Cache-Control'] = 'private'
        return resp
