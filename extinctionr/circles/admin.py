from django.contrib import admin
from .models import Circle
from markdownx.admin import MarkdownxModelAdmin


@admin.register(Circle)
class CircleAdmin(MarkdownxModelAdmin):
    list_display = ('__str__', 'modified')
    readonly_fields = ('created', 'modified', )
    list_select_related = ('parent',)
    search_fields = ('name', )
    autocomplete_fields = ('leads', 'members', 'parent')
