from django.shortcuts import redirect

def redirect_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        if response.status_code == 404 and request.META['QUERY_STRING']:
            response = redirect(request.path)
        return response

    return middleware
