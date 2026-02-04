from django.db import models
from django.contrib.auth.models import User


class NewsSource(models.Model):
    """新闻来源"""
    SOURCE_TYPES = [
        ('api', 'API'),
        ('rss', 'RSS'),
        ('manual', '手动'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_sources', verbose_name='用户')
    name = models.CharField(max_length=100, verbose_name='来源名称')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='api', verbose_name='来源类型')
    api_url = models.URLField(blank=True, verbose_name='API 地址')
    api_key = models.CharField(max_length=500, blank=True, verbose_name='API 密钥')
    config = models.JSONField(default=dict, blank=True, verbose_name='配置')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '新闻来源'
        verbose_name_plural = '新闻来源'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    """新闻文章"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_articles', verbose_name='用户')
    source = models.ForeignKey(NewsSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles', verbose_name='来源')
    title = models.CharField(max_length=500, verbose_name='标题')
    link = models.URLField(verbose_name='原文链接')
    summary = models.TextField(blank=True, verbose_name='摘要')
    content = models.TextField(blank=True, verbose_name='内容')
    author = models.CharField(max_length=100, blank=True, verbose_name='作者')
    category = models.CharField(max_length=50, blank=True, verbose_name='分类')
    image_url = models.URLField(blank=True, verbose_name='图片')
    published_at = models.DateTimeField(verbose_name='发布时间')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    is_starred = models.BooleanField(default=False, verbose_name='收藏')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '新闻文章'
        verbose_name_plural = '新闻文章'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class NewsCategory(models.Model):
    """新闻分类"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_categories', verbose_name='用户')
    name = models.CharField(max_length=50, verbose_name='分类名称')
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name='颜色')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '新闻分类'
        verbose_name_plural = '新闻分类'
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name
