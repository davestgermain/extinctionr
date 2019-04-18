from django.urls import path, include
from .views import InfoView, PRListView, PRDetailView

app_name = 'extinctionr.info'

urlpatterns = [
    path('pr/', PRListView.as_view(), name='pr-list'),
    path('pr/<str:slug>', PRDetailView.as_view(), name='pr-detail'),
    path('', InfoView.as_view(), kwargs={'page': 'home'}, name='index'),
    path('<path:page>', InfoView.as_view(), name='page'),
]
