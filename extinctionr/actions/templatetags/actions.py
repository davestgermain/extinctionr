from django import template
from django.utils.timezone import now
from extinctionr.actions import models


register = template.Library()

@register.inclusion_tag('recent_actions.html')
def recent_actions(*args, **kwargs):
    adverb = kwargs.get('adverb', 'recent')
    ract = models.Action.objects.filter(public=True).order_by('when')
    if adverb == 'recent':
        ract = ract.filter(when__lte=now())
    else:
        ract = ract.filter(when__gte=now())
    return {'actions': ract, 'adverb': adverb.capitalize()}
