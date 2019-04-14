from django.contrib import admin
from .models import PressRelease, Photo
from markdownx.admin import MarkdownxModelAdmin


@admin.register(PressRelease)
class PressReleaseAdmin(MarkdownxModelAdmin):
    list_display = ('slug', 'title', 'released')
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ('modified', )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    readonly_fields = ('uploader', 'thumbnail_tag')
    list_display = ('created', 'uploader', 'caption', 'thumbnail_tag')

    def save_model(self, request, obj, form, change):
        obj.uploader = request.user
        super().save_model(request, obj, form, change)
