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
    return {'actions': ract[:10], 'adverb': adverb.capitalize()}


@register.inclusion_tag('highlight_action.html')
def highlight_action(*args, **kwargs):
    try:
        action = models.Action.objects.filter(public=True, tags__name='highlight', when__gte=now())[0]
    except IndexError:
        action = None
    return {'action': action}

@register.inclusion_tag('month_actions.json')
def month_actions(actions):
    return {'actions' : actions}
