from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from markdownx.utils import markdownify

register = template.Library()


@register.filter('markdownify')
def _markdownify(content):
    return mark_safe(markdownify(strip_tags(content)))
