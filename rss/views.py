import feedparser
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import RSSFeed, RSSArticle


@login_required
def feed_list(request):
    """RSS 订阅源列表"""
    feeds = RSSFeed.objects.filter(user=request.user).annotate(
        article_count=models.Count('articles'),
        unread_count=models.Count('articles', filter=models.Q(articles__is_read=False))
    ).order_by('-created_at')
    
    context = {
        'feeds': feeds,
    }
    return render(request, 'rss/feed_list.html', context)


@login_required
def feed_add(request):
    """添加 RSS 订阅源"""
    if request.method == 'POST':
        url = request.POST.get('url')
        title = request.POST.get('title', '')
        
        if not url:
            messages.error(request, '请输入 RSS 链接')
            return redirect('rss:feed_add')
        
        # 检查是否已存在
        if RSSFeed.objects.filter(user=request.user, url=url).exists():
            messages.error(request, '该 RSS 源已存在')
            return redirect('rss:feed_add')
        
        try:
            # 解析 RSS
            feed_data = feedparser.parse(url)
            
            # 更宽松的验证 - 只要有标题或文章就认为有效
            has_valid_data = False
            
            # 检查 feed 标题
            feed_title = ''
            if hasattr(feed_data, 'feed') and feed_data.feed:
                if hasattr(feed_data.feed, 'title') and feed_data.feed.title:
                    feed_title = feed_data.feed.title
                    has_valid_data = True
            
            # 检查是否有文章
            if hasattr(feed_data, 'entries') and feed_data.entries and len(feed_data.entries) > 0:
                has_valid_data = True
            
            # 如果 bozo 异常且没有任何有效数据，才报错
            if feed_data.bozo and not has_valid_data:
                messages.error(request, '无法解析该 RSS 源，请检查链接是否正确')
                return redirect('rss:feed_add')
            
            # 获取 feed 描述
            feed_description = ''
            if hasattr(feed_data, 'feed') and feed_data.feed:
                if hasattr(feed_data.feed, 'description') and feed_data.feed.description:
                    feed_description = feed_data.feed.description
                elif hasattr(feed_data.feed, 'subtitle') and feed_data.feed.subtitle:
                    feed_description = feed_data.feed.subtitle
            
            # 创建订阅源
            feed = RSSFeed.objects.create(
                user=request.user,
                title=title or feed_title or '未命名订阅',
                url=url,
                description=feed_description,
            )
            
            # 获取文章
            fetch_feed_articles(feed, feed_data)
            
            messages.success(request, f'成功添加订阅源：{feed.title}')
            return redirect('rss:feed_list')
            
        except Exception as e:
            messages.error(request, f'添加失败：{str(e)}')
            return redirect('rss:feed_add')
    
    return render(request, 'rss/feed_add.html')


@login_required
def feed_detail(request, pk):
    """订阅源详情"""
    feed = get_object_or_404(RSSFeed, pk=pk, user=request.user)
    articles = feed.articles.all()
    
    # 筛选
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        articles = articles.filter(is_read=False)
    elif filter_type == 'starred':
        articles = articles.filter(is_starred=True)
    
    context = {
        'feed': feed,
        'articles': articles[:50],
        'filter_type': filter_type,
    }
    return render(request, 'rss/feed_detail.html', context)


@login_required
def feed_edit(request, pk):
    """编辑订阅源"""
    feed = get_object_or_404(RSSFeed, pk=pk, user=request.user)
    
    if request.method == 'POST':
        feed.title = request.POST.get('title', feed.title)
        feed.description = request.POST.get('description', feed.description)
        feed.is_active = request.POST.get('is_active') == 'on'
        feed.save()
        
        messages.success(request, '订阅源已更新')
        return redirect('rss:feed_detail', pk=feed.pk)
    
    return render(request, 'rss/feed_edit.html', {'feed': feed})


@login_required
def feed_delete(request, pk):
    """删除订阅源"""
    feed = get_object_or_404(RSSFeed, pk=pk, user=request.user)
    
    if request.method == 'POST':
        feed.delete()
        messages.success(request, '订阅源已删除')
        return redirect('rss:feed_list')
    
    return render(request, 'rss/feed_delete.html', {'feed': feed})


@login_required
def feed_refresh(request, pk):
    """刷新订阅源"""
    feed = get_object_or_404(RSSFeed, pk=pk, user=request.user)
    
    try:
        import feedparser
        feed_data = feedparser.parse(feed.url)
        
        # 检查是否成功获取到数据
        if hasattr(feed_data, 'bozo_exception') and feed_data.bozo:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"RSS parse warning for {feed.url}: {feed_data.bozo_exception}")
        
        fetch_feed_articles(feed, feed_data)
        feed.last_fetched = timezone.now()
        feed.save()
        
        # 获取更新的文章数量
        article_count = feed.articles.count()
        messages.success(request, f'已更新 {feed.title}，共 {article_count} 篇文章')
    except Exception as e:
        messages.error(request, f'更新失败：{str(e)}')
    
    return redirect('rss:feed_detail', pk=feed.pk)


@login_required
def article_list(request):
    """所有 RSS 文章列表"""
    articles = RSSArticle.objects.filter(feed__user=request.user)
    
    # 筛选
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        articles = articles.filter(is_read=False)
    elif filter_type == 'starred':
        articles = articles.filter(is_starred=True)
    
    # 按订阅源筛选
    feed_id = request.GET.get('feed')
    if feed_id:
        articles = articles.filter(feed_id=feed_id)
    
    context = {
        'articles': articles[:100],
        'filter_type': filter_type,
        'feeds': RSSFeed.objects.filter(user=request.user),
        'selected_feed': feed_id,
    }
    return render(request, 'rss/article_list.html', context)


@login_required
def article_detail(request, pk):
    """文章详情"""
    article = get_object_or_404(RSSArticle, pk=pk, feed__user=request.user)
    
    # 标记为已读
    if not article.is_read:
        article.is_read = True
        article.save()
    
    context = {
        'article': article,
    }
    return render(request, 'rss/article_detail.html', context)


@require_POST
@login_required
def article_toggle_star(request, pk):
    """切换收藏状态"""
    article = get_object_or_404(RSSArticle, pk=pk, feed__user=request.user)
    article.is_starred = not article.is_starred
    article.save()
    
    return JsonResponse({'success': True, 'is_starred': article.is_starred})


@require_POST
@login_required
def article_toggle_read(request, pk):
    """切换已读状态"""
    article = get_object_or_404(RSSArticle, pk=pk, feed__user=request.user)
    article.is_read = not article.is_read
    article.save()
    
    return JsonResponse({'success': True, 'is_read': article.is_read})


@login_required
def article_delete(request, pk):
    """删除文章"""
    article = get_object_or_404(RSSArticle, pk=pk, feed__user=request.user)
    article.delete()
    messages.success(request, '文章已删除')
    return redirect('rss:article_list')


def fetch_feed_articles(feed, feed_data):
    """获取订阅源文章"""
    from django.utils.dateparse import parse_datetime
    import time
    from datetime import datetime
    
    for entry in feed_data.entries[:50]:  # 最多获取 50 篇
        # 获取发布时间 - 支持多种格式
        published_at = None
        
        # 尝试不同的发布时间字段
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = timezone.make_aware(datetime(*entry.published_parsed[:6]))
            except (ValueError, TypeError):
                pass
        
        if not published_at and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_at = timezone.make_aware(datetime(*entry.updated_parsed[:6]))
            except (ValueError, TypeError):
                pass
        
        # 尝试解析 published 字符串
        if not published_at and hasattr(entry, 'published') and entry.published:
            try:
                published_at = parse_datetime(entry.published)
            except:
                pass
        
        # 尝试解析 updated 字符串
        if not published_at and hasattr(entry, 'updated') and entry.updated:
            try:
                published_at = parse_datetime(entry.updated)
            except:
                pass
        
        # 如果都失败了，使用当前时间
        if not published_at:
            published_at = timezone.now()
        
        # 获取内容 - 支持多种格式
        content = ''
        
        # 尝试 content 字段（可能是列表或字符串）
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                content = entry.content[0].get('value', '') if isinstance(entry.content[0], dict) else str(entry.content[0])
            elif isinstance(entry.content, str):
                content = entry.content
        
        # 尝试 content_encoded (一些 RSS 源使用这个字段)
        if not content and hasattr(entry, 'content_encoded') and entry.content_encoded:
            content = entry.content_encoded
        
        # 尝试 description 字段
        if not content and hasattr(entry, 'description') and entry.description:
            content = entry.description
        
        # 尝试 summary 字段
        if not content and hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        
        # 获取摘要
        description = ''
        if hasattr(entry, 'summary') and entry.summary:
            description = entry.summary
        elif hasattr(entry, 'description') and entry.description:
            description = entry.description
        elif content:
            # 从内容生成摘要
            description = content[:500]
        
        # 清理 HTML 标签
        import re
        description = re.sub(r'<[^>]+>', '', description)
        
        # 获取链接 - 支持多种格式
        link = ''
        if hasattr(entry, 'link') and entry.link:
            link = entry.link
        elif hasattr(entry, 'links') and entry.links:
            for l in entry.links:
                if isinstance(l, dict) and l.get('rel') == 'alternate':
                    link = l.get('href', '')
                    break
                elif isinstance(l, dict) and l.get('href'):
                    link = l.get('href')
                    break
        
        # 获取标题
        title = ''
        if hasattr(entry, 'title') and entry.title:
            title = entry.title
            # 清理 HTML 标签
            title = re.sub(r'<[^>]+>', '', title)
        
        if not title:
            title = '无标题'
        
        # 获取作者
        author = ''
        if hasattr(entry, 'author') and entry.author:
            author = entry.author
        elif hasattr(entry, 'author_detail') and entry.author_detail:
            author = entry.author_detail.get('name', '') if isinstance(entry.author_detail, dict) else str(entry.author_detail)
        
        # 创建或更新文章
        if link:  # 只有有链接才创建
            RSSArticle.objects.get_or_create(
                feed=feed,
                link=link[:2000],
                defaults={
                    'title': title[:500],
                    'description': description[:2000],
                    'content': content[:10000],
                    'author': author[:100],
                    'published_at': published_at,
                }
            )


# 导入 models
from django.db import models
