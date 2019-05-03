from django.contrib import admin
from .models import Circle, MembershipRequest
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Circle)
class CircleAdmin(MarkdownxModelAdmin):
    list_display = ('__str__', 'modified')
    readonly_fields = ('created', 'modified', )
    list_select_related = ('parent',)
    search_fields = ('name', )
    autocomplete_fields = ('leads', 'members', 'parent')
    fields = ('name', 'parent', 'purpose', 'sensitive_info', 'email', 'leads', 'members', 'color', 'created', 'modified')

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.can_manage(request.user)
        else:
            return request.user.has_perm('circles.change_circle')


@admin.register(MembershipRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('created', 'requestor', 'circle', 'confirmed_by', 'confirm_date')
    list_select_related = ('requestor', 'circle')
    autocomplete_fields = ('requestor', 'confirmed_by', 'circle')
    readonly_fields = ('confirm_date', )
