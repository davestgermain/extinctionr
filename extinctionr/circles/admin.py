from django.contrib import admin
from .models import Circle, CircleMember, MembershipRequest
from extinctionr.utils import get_contact
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Circle)
class CircleAdmin(MarkdownxModelAdmin):
    list_display = ('__str__', 'modified')
    readonly_fields = ('created', 'modified', )
    list_select_related = ('parent',)
    search_fields = ('name', )
    autocomplete_fields = ('parent', )
    fields = ('name', 'parent', 'purpose', 'sensitive_info', 'email', 'available_roles', 'role_description', 'color', 'created', 'modified')

    def has_view_permission(self, request, obj=None):
        if obj:
            return obj.can_manage(request.user)
        else:
            return request.user.has_perm('circles.view_circle')

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.can_manage(request.user)
        else:
            return request.user.has_perm('circles.change_circle')

    def has_module_permission(self, request):
        contact = get_contact(email=request.user.email)
        return contact.circlemember_set.exists()


@admin.register(MembershipRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('created', 'requestor', 'circle', 'confirmed_by', 'confirm_date')
    list_select_related = ('requestor', 'circle')
    autocomplete_fields = ('requestor', 'confirmed_by', 'circle')
    readonly_fields = ('confirm_date', )


@admin.register(CircleMember)
class CircleMemberAdmin(admin.ModelAdmin):
    list_display = ('circle', 'contact', 'role', 'join_date')
    autocomplete_fields = ('circle', 'contact')
    readonly_fields = ('join_date', )
    list_filter = ('circle',)
