from django.contrib import admin
from .models import Action, ActionRole, Attendee, TalkProposal
from markdownx.admin import MarkdownxModelAdmin
from contacts.models import Contact


@admin.register(Action)
class ActionAdmin(MarkdownxModelAdmin):
    list_display = ('slug', 'name', 'when')
    prepopulated_fields = {"slug": ("name",)}
    filter_vertical = ('photos',)
    readonly_fields = ('modified', )


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


admin.site.unregister(Contact)
# overriding the default admin to add some features
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
	search_fields = ('first_name', 'last_name', 'email')
	list_display = ('email', 'first_name', 'last_name', 'phone', 'created_on')
	list_filter = ('address__state', 'address__city')
	list_select_related = ('address', )


def _contact_str(obj):
	return '{} {}'.format(obj.first_name, obj.last_name)

Contact.__str__ = _contact_str
