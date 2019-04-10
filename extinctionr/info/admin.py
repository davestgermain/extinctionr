from django.contrib import admin
from .models import PressRelease
from markdownx.admin import MarkdownxModelAdmin


@admin.register(PressRelease)
class PressReleaseAdmin(MarkdownxModelAdmin):
	list_display = ('slug', 'title', 'released')
	prepopulated_fields = {"slug": ("title",)}

