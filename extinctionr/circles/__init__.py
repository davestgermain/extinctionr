

def get_circle(name):
    from .models import Circle
    try:
        return Circle.objects.filter(name__istartswith=name).order_by('name', '-id')[0]
    except IndexError:
        return None
