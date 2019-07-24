from django.urls import include, path

from .views import InfoView, PRDetailView, PRListView, RegistrationView, ContactView

app_name = 'extinctionr.info'

urlpatterns = [
    path('pr/', PRListView.as_view(), name='pr-list'),
    path('pr/<str:slug>', PRDetailView.as_view(), name='pr-detail'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('contact', ContactView.as_view(), name="contact"),
    path('', InfoView.as_view(), kwargs={'page': 'home'}, name='index'),
    path('<path:page>', InfoView.as_view(), name='page'),
]
