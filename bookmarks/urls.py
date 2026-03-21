from django.urls import path
from . import views

app_name = 'bookmarks'

urlpatterns = [
    # 公开书签页面（无需登录）
    path('public/', views.bookmark_public, name='bookmark_public'),

    # 书签列表与CRUD
    path('', views.bookmark_list, name='bookmark_list'),
    path('add/', views.bookmark_add, name='bookmark_add'),
    path('quick-add/', views.bookmark_quick_add, name='bookmark_quick_add'),
    path('<int:pk>/', views.bookmark_detail, name='bookmark_detail'),
    path('<int:pk>/edit/', views.bookmark_edit, name='bookmark_edit'),
    path('<int:pk>/delete/', views.bookmark_delete, name='bookmark_delete'),
    path('<int:pk>/pin/', views.bookmark_toggle_pin, name='bookmark_toggle_pin'),
    path('<int:pk>/privacy/', views.bookmark_toggle_privacy, name='bookmark_toggle_privacy'),
    path('<int:pk>/visit/', views.bookmark_visit, name='bookmark_visit'),

    # 分类管理
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
]