from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import Photo, PressRelease, Chapter


@admin.register(PressRelease)
class PressReleaseAdmin(MarkdownxModelAdmin):
    list_display = ('slug', 'title', 'released')
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ('modified', )


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    readonly_fields = ('uploader', 'thumbnail_tag', 'width', 'height')
    list_display = ('created', 'uploader', 'caption', 'thumbnail_tag')

    def save_model(self, request, obj, form, change):
        obj.uploader = request.user
        super().save_model(request, obj, form, change)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'site')