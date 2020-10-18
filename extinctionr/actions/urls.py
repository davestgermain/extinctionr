from django.urls import path, include
from . import views

app_name = 'extinctionr.actions'

urlpatterns = [
    path('talk/', views.propose_talk, name='talk-proposal'),
    path('talk/<int:talk_id>/respond', views.talk_respond, name='talk-respond'),
    path('talk/<int:talk_id>/convert', views.convert_proposal_to_action, name='talk-convert'),
    path('talk/list/', views.list_proposals, name='list-talk-proposals'),
    path('', views.list_actions, name='list-actions'),
    path('ical/<str:whatever>', views.calendar_view, name='calendar-actions'),
    path('ics/<str:slug>', views.action_ics_view, name='calendar-action'),
    path('<str:slug>/', views.show_action, name='action'),
    path('<str:action_slug>/attendees/', views.show_attendees, name='attendees'),
    path('<str:action_slug>/attendees/mark/', views.mark_promised, name='mark-attendee'),
    path('<str:action_slug>/attendees/notify/', views.send_notifications, name='notify-attendees'),
]
