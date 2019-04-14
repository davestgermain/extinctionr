from django.contrib import admin
from .models import Action, ActionRole, Attendee, TalkProposal
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Action)
class ActionAdmin(MarkdownxModelAdmin):
    list_display = ('slug', 'name', 'when')
    prepopulated_fields = {"slug": ("name",)}
    filter_vertical = ('photos',)
    readonly_fields = ('modified', )


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('action', 'contact', 'role', 'promised')

@admin.register(TalkProposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('created', 'requestor', 'location', 'responded')

admin.site.register(ActionRole)
