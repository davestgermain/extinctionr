from django.urls import path, include
from .views import signup_form, show_action, show_attendees

app_name = 'extinctionr.actions'

urlpatterns = [
    path('<str:slug>/', show_action, name='action'),
    path('<str:action_slug>/signup/', signup_form, name='signup'),
    path('<str:action_slug>/attendees/', show_attendees, name='attendees'),
]
