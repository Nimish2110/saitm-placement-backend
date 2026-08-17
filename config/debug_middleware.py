import traceback
from django.http import HttpResponse

class ShowErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        return HttpResponse(traceback.format_exc(), content_type="text/plain", status=500)