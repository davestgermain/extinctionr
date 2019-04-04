from django.urls import path, include
from .views import InfoView

app_name = 'extinctionr.info'

urlpatterns = [
    path('', InfoView.as_view(), kwargs={'page': 'index'}, name='index'),
    path('<str:page>', InfoView.as_view(), name='page'),
]
