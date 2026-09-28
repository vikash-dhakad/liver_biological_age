"""
URL configuration for Liver Proteomics Aging Portal.
"""
import os
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

FRONTEND_DIR = os.path.join(settings.BASE_DIR.parent, 'frontend')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Direct static file serving for /css/ and /js/
    re_path(r'^(?P<path>(css|js)/.*)$', serve, {'document_root': FRONTEND_DIR}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=FRONTEND_DIR)
