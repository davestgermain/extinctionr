"""extinctionr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from django.contrib.auth import views
from extinctionr.actions.views import propose_talk

from common.views import handler404, handler500

app_name = 'extinctionr'

urlpatterns = [
    path('talk', propose_talk),
    path('', include('django.contrib.auth.urls')),
    path('', include('extinctionr.info.urls', namespace='extinctionr.info')),
    path('action/', include('extinctionr.actions.urls', namespace="actions")),
    path('relationships/', include('common.urls', namespace="common")),
    path('relationships/m/', include('marketing.urls', namespace="marketing")),
    path('relationships/accounts/', include('accounts.urls', namespace="accounts")),
    path('relationships/leads/', include('leads.urls', namespace="leads")),
    path('relationships/contacts/', include('contacts.urls', namespace="contacts")),
    path('relationships/opportunities/',
         include('opportunity.urls', namespace="opportunities")),
    path('relationships/cases/', include('cases.urls', namespace="cases")),
    path('relationships/emails/', include('emails.urls', namespace="emails")),
    # path('planner/', include('planner.urls', namespace="planner")),
    path('admin/', admin.site.urls),
    path('notifications/', include('django_nyt.urls')),
    path('wiki/', include('wiki.urls')),
    path('markdownx/', include('markdownx.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls))
        ] + urlpatterns
    except ImportError:
        pass
