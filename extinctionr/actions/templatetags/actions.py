from django import template
from django.utils.timezone import now
from extinctionr.actions import models


register = template.Library()

@register.inclusion_tag('recent_actions.html')
def recent_actions(*args, **kwargs):
    adverb = kwargs.get('adverb', 'recent')
    ract = models.Action.objects.filter(public=True)
    if adverb == 'recent':
        ract = ract.filter(when__lte=now()).order_by('-when')
    else:
        ract = ract.filter(when__gte=now()).order_by('when')
    return {'actions': ract, 'adverb': adverb.capitalize()}
