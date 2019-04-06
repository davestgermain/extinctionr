from django.contrib import admin
from .models import Action, ActionRole, Attendee
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Action)
class ActionAdmin(MarkdownxModelAdmin):
	list_display = ('slug', 'name', 'when')
	prepopulated_fields = {"slug": ("name",)}


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
	list_display = ('action', 'contact', 'role', 'promised')

admin.site.register(ActionRole)

