from django.contrib import admin
from django.db import models
from django import forms
from .models import Action, ActionRole, Attendee, TalkProposal
from markdownx.admin import MarkdownxModelAdmin
from contacts.models import Contact


@admin.register(Action)
class ActionAdmin(MarkdownxModelAdmin):
    list_display = ('slug', 'name', 'when')
    prepopulated_fields = {"slug": ("name",)}
    filter_vertical = ('photos',)
    readonly_fields = ('modified', )
    # formfield_overrides = {
    #     models.DateTimeField: {'widget': forms.DateTimeInput},
    # }


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('action', 'contact', 'role', 'promised')
    list_filter = ('action__name',)
    list_select_related = ('action', 'contact')
    autocomplete_fields = ('contact',)
    search_fields = ('action__name', 'contact__email')


@admin.register(TalkProposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('created', 'requestor', 'location', 'responded')
    search_fields = ('requestor__first_name', 'requestor__email')
    list_select_related = ('requestor',)
    autocomplete_fields = ('requestor',)

admin.site.register(ActionRole)

