from django.urls import path, include
from .views import signup_form, show_action

app_name = 'extinctionr.actions'

urlpatterns = [
    path('<int:action_id>/', show_action, name='action'),
    path('<int:action_id>/signup/', signup_form, name='signup'),
]
