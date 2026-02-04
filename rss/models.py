from django.db import models
from django.contrib.auth.models import User


class RSSFeed(models.Model):
    """RSS 订阅源"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rss_feeds', verbose_name='用户')
    title = models.CharField(max_length=200, verbose_name='标题')
    url = models.URLField(verbose_name='RSS 链接')
    description = models.TextField(blank=True, verbose_name='描述')
    favicon = models.URLField(blank=True, verbose_name='图标')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    last_fetched = models.DateTimeField(null=True, blank=True, verbose_name='最后获取时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'RSS 订阅源'
        verbose_name_plural = 'RSS 订阅源'
        ordering = ['-created_at']
        unique_together = ['user', 'url']

    def __str__(self):
        return self.title


class RSSArticle(models.Model):
    """RSS 文章"""
    feed = models.ForeignKey(RSSFeed, on_delete=models.CASCADE, related_name='articles', verbose_name='订阅源')
    title = models.CharField(max_length=500, verbose_name='标题')
    link = models.URLField(verbose_name='原文链接')
    description = models.TextField(blank=True, verbose_name='摘要')
    content = models.TextField(blank=True, verbose_name='内容')
    author = models.CharField(max_length=100, blank=True, verbose_name='作者')
    published_at = models.DateTimeField(verbose_name='发布时间')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    is_starred = models.BooleanField(default=False, verbose_name='收藏')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'RSS 文章'
        verbose_name_plural = 'RSS 文章'
        ordering = ['-published_at']
        unique_together = ['feed', 'link']

    def __str__(self):
        return self.title
