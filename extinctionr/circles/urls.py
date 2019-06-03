from django.urls import path
from . import views

app_name = 'circles' 

urlpatterns = [
    path('', views.TopLevelView.as_view(), name='outer'),
    path('person/<int:contact_id>/', views.person_view, name='person'),
    path('person/me/', views.person_view, name='person-me'),
    path('person/import/', views.csv_import, name='person-import'),
    path('person/export/', views.csv_export, name='person-export'),
    path('person/autocomplete/', views.ContactAutocomplete.as_view(), name='person-autocomplete'),
    path('person/find/', views.FindFormView.as_view(), name='find-person'),
    path('jobs/', views.JobView.as_view(), name='jobs'),
    path('<int:pk>/', views.CircleView.as_view(), name='detail'),
    path('<int:pk>/join/', views.request_membership, name='request-membership'),
    path('<int:pk>/add/', views.add_member, name='add-member'),
    path('<int:pk>/del/', views.del_member, name='del-member'),
    path('<int:pk>/approve/', views.approve_membership, name='approve-member'),
]
