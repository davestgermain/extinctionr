from django.urls import path, include
from . import views

app_name = 'extinctionr.actions'

urlpatterns = [
    path('talk/', views.propose_talk, name='talk-proposal'),
    path('talk/list/', views.list_proposals, name='list-talk-proposals'),
    path('<str:slug>/', views.show_action, name='action'),
    path('<str:action_slug>/signup/', views.signup_form, name='signup'),
    path('<str:action_slug>/attendees/', views.show_attendees, name='attendees'),
]
