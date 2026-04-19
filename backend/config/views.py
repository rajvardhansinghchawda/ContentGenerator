from django.http import HttpResponse

def health_check(request):
    """
    Simple health check endpoint for Render/deployment monitoring.
    Returns 200 OK.
    """
    return HttpResponse("OK", status=200)
