from django.urls import path
from . import views

app_name = 'rss'

urlpatterns = [
    # Feed URLs
    path('', views.feed_list, name='feed_list'),
    path('add/', views.feed_add, name='feed_add'),
    path('<int:pk>/', views.feed_detail, name='feed_detail'),
    path('<int:pk>/edit/', views.feed_edit, name='feed_edit'),
    path('<int:pk>/delete/', views.feed_delete, name='feed_delete'),
    path('<int:pk>/refresh/', views.feed_refresh, name='feed_refresh'),
    
    # Article URLs
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/star/', views.article_toggle_star, name='article_toggle_star'),
    path('articles/<int:pk>/read/', views.article_toggle_read, name='article_toggle_read'),
    path('articles/<int:pk>/delete/', views.article_delete, name='article_delete'),
]
