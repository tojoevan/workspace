"""
URL configuration for reading_workbench project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core
    path('', core_views.dashboard, name='dashboard'),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('search/', core_views.search, name='search'),
    path('api-docs/', core_views.api_docs, name='api_docs'),
    path('user/profile/', core_views.user_profile, name='user_profile'),
    path('user/check-alias/', core_views.check_alias, name='check_alias'),

    # Apps
    path('rss/', include('rss.urls')),
    path('news/', include('news.urls')),
    path('notes/', include('notes.urls')),

    # API
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
