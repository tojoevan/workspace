from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # API 状态
    path('v1/status/', views.api_status, name='api_status'),
    
    # 获取 API 密钥
    path('v1/key/', views.get_api_key, name='get_api_key'),
    
    # 推送新闻
    path('v1/news/push/', views.push_news, name='push_news'),
    path('v1/news/push/batch/', views.push_news_batch, name='push_news_batch'),
]
