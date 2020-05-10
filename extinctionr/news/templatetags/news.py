from django import template

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


