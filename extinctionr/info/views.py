from hashlib import md5

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core import serializers
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template.loader import TemplateDoesNotExist, get_template
from django.utils.decorators import method_decorator
from django.utils.http import http_date
from django.views.decorators.http import etag
from django.views.decorators.cache import cache_page
from django.views.generic import FormView, DetailView, ListView, TemplateView

from .models import PressRelease, Chapter


class RegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("email",)
        field_classes = {'email': forms.EmailField}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class ContactForm(forms.Form):
    message = forms.CharField()


class RegistrationView(FormView):
    form_class = RegistrationForm
    success_url = '/'
    template_name = 'registration/register.html'

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)


class ContactView(FormView):
    form_class = ContactForm
    success_url = '/contact'
    template_name = 'info/contact.html'

    def form_valid(self, form):
        from django.conf import settings
        from django.core.mail import send_mail
        from extinctionr.circles import get_circle
        outreach_circle = get_circle('outreach')
        address = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', 'unknown address'))
        subject = '[XR] Website Contact from {}'.format(address)
        message = form.cleaned_data['message']
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, outreach_circle.get_notification_addresses())
        messages.success(self.request, "Thanks for your feedback")
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
        response['Vary'] = 'Cookie'
        if request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


@method_decorator(cache_page(1200), name='dispatch')
class PRListView(ListView):
    def get_queryset(self):
        if self.request.user.has_perm('info.view_pressrelease'):
            return PressRelease.objects.all().order_by('-released')
        else:
            return PressRelease.objects.released()

    def render_to_response(self, context, **kwargs):
        resp = super().render_to_response(context, **kwargs)
        resp['Last-Modified'] = http_date(context['object_list'].last().modified.timestamp())
        resp['Vary'] = 'Cookie'
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
        resp['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            resp['Cache-Control'] = 'private'
        return resp

def list_chapters(request):
    chapters = serializers.serialize("json", Chapter.objects.all())
    context = {'chapters': chapters }
    return render(request, 'pages/groups/index.html', context)
