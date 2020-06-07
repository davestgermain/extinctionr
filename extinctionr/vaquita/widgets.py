from django import forms

from wagtailmarkdown.widgets import MarkdownTextarea


class ZOrderMarkdownTextarea(MarkdownTextarea):
    @property
    def media(self):
        media = super().media
        return media + forms.Media(
            css={'all': ('css/xr-codemirror.css',)}
        )


class XRColorPicker(forms.TextInput):
    template_name = "forms/widgets/color_picker.html"

    class Media:
        css = {
            'all': ('css/xr-color-picker.css',)
        }
        js = ('js/xr-color-picker.js',)
