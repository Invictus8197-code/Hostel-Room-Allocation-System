from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import os

def render_react(request):
    try:
        with open(os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')) as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse(
            "Frontend build not found. Please run 'npm install' and 'npm run build' inside the 'frontend' folder.", 
            status=501
        )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.apps.api.urls')),
    re_path(r'^.*$', render_react), # Catch-all to serve React SPA
]
