from django.contrib import admin
from .models import Action, ActionRole, Attendee


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
	list_display = ('name', 'when')


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
	list_display = ('action', 'contact', 'role')

admin.site.register(ActionRole)

