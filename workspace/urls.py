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
    path('', core_views.home, name='home'),
    path('workspace/', core_views.workspace, name='workspace'),
    path('ws/', core_views.workspace, name='workspace_short'),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('search/', core_views.search, name='search'),
    path('api-docs/', core_views.api_docs, name='api_docs'),
    path('user/profile/', core_views.user_profile, name='user_profile'),
    path('user/check-alias/', core_views.check_alias, name='check_alias'),
    path('article/toggle-star/', core_views.toggle_article_star, name='toggle_article_star'),
    path('article/toggle-read-later/', core_views.toggle_article_read_later, name='toggle_article_read_later'),
    path('article/mark-read/', core_views.mark_article_read, name='mark_article_read'),
    path('article/mark-all-read/', core_views.mark_all_read, name='mark_all_read'),

    # Apps
    path('rss/', include('rss.urls')),
    path('news/', include('news.urls')),
    path('notes/', include('notes.urls')),
    path('todos/', include('todo.urls')),
    path('bookmarks/', include('bookmarks.urls')),

    # API
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
