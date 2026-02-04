from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # Source URLs
    path('sources/', views.source_list, name='source_list'),
    path('sources/add/', views.source_add, name='source_add'),
    path('sources/<int:pk>/edit/', views.source_edit, name='source_edit'),
    path('sources/<int:pk>/delete/', views.source_delete, name='source_delete'),
    path('sources/<int:pk>/refresh/', views.source_refresh, name='source_refresh'),
    
    # Article URLs
    path('', views.article_list, name='article_list'),
    path('<int:pk>/', views.article_detail, name='article_detail'),
    path('<int:pk>/star/', views.article_toggle_star, name='article_toggle_star'),
    path('<int:pk>/read/', views.article_toggle_read, name='article_toggle_read'),
    path('<int:pk>/delete/', views.article_delete, name='article_delete'),
    
    # Import
    path('import/', views.import_from_api, name='import_from_api'),
]
