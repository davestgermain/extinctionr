import urllib
from django import template
from extinctionr.news.models import FeaturedStory

register = template.Library()

@register.filter('elide_pages')
def elide_pages(range, page):
    xs = []
    skip = False
    for x in range:
        if x <= 2 or x >= range.stop - 2:
            xs.append(x)
            skip = False
        elif page-3 <= x <= page+3:
            xs.append(x)
            skip = False
        elif not skip:        
            xs.append(-1)
            skip = True
    return xs

@register.filter('share_url')
def share_url(story, service):
    pageurl = story.get_full_url()
    if service == 'fb':
        return 'https://www.facebook.com/sharer/sharer.php?u={0}'.format(pageurl)
    if service == 'twitter':
        title = urllib.parse.quote(story.title)
        url = 'https://twitter.com/share?url={0}&text={1}&hashtags={2}'.format(
            pageurl, title, 'ExtinctionRebellion,XRBoston'
        )
        return url
    if service == 'email':
        url = 'mailto:?subject=' + story.title + '-' + pageurl
        url += '&body=' + story.title + '%0D%0A' + pageurl
        return url


@register.inclusion_tag("news/story_sidebar.html")
def story_sidebar(*args, **kwargs):
    featured = FeaturedStory.objects.all().order_by('-story__first_published_at')
    return {'featured_stories': featured}

@register.inclusion_tag("news/story_mini_card.html")
def mini_card(story):
    return {'story' : story.specific}
