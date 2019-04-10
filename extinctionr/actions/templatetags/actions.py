from django import template
from django.utils.timezone import now
from extinctionr.actions import models


register = template.Library()

@register.inclusion_tag('recent_actions.html')
def recent_actions():
    ract = models.Action.objects.filter(public=True, when__lte=now()).order_by('when')
    return {'recent': ract}
