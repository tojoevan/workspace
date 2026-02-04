import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import NewsSource, NewsArticle, NewsCategory


@login_required
def source_list(request):
    """新闻来源列表"""
    sources = NewsSource.objects.filter(user=request.user).annotate(
        article_count=models.Count('articles')
    ).order_by('-created_at')
    
    context = {
        'sources': sources,
    }
    return render(request, 'news/source_list.html', context)


@login_required
def source_add(request):
    """添加新闻来源"""
    if request.method == 'POST':
        name = request.POST.get('name')
        source_type = request.POST.get('source_type', 'api')
        api_url = request.POST.get('api_url', '')
        api_key = request.POST.get('api_key', '')
        
        if not name:
            messages.error(request, '请输入来源名称')
            return redirect('news:source_add')
        
        try:
            source = NewsSource.objects.create(
                user=request.user,
                name=name,
                source_type=source_type,
                api_url=api_url,
                api_key=api_key,
            )
            
            # 如果是 API 类型，尝试获取新闻
            if source_type == 'api' and api_url:
                fetch_news_from_api(source)
            
            messages.success(request, f'成功添加新闻来源：{name}')
            return redirect('news:source_list')
            
        except Exception as e:
            messages.error(request, f'添加失败：{str(e)}')
            return redirect('news:source_add')
    
    return render(request, 'news/source_add.html')


@login_required
def source_edit(request, pk):
    """编辑新闻来源"""
    source = get_object_or_404(NewsSource, pk=pk, user=request.user)
    
    if request.method == 'POST':
        source.name = request.POST.get('name', source.name)
        source.api_url = request.POST.get('api_url', source.api_url)
        source.api_key = request.POST.get('api_key', source.api_key)
        source.is_active = request.POST.get('is_active') == 'on'
        source.save()
        
        messages.success(request, '新闻来源已更新')
        return redirect('news:source_list')
    
    return render(request, 'news/source_edit.html', {'source': source})


@login_required
def source_delete(request, pk):
    """删除新闻来源"""
    source = get_object_or_404(NewsSource, pk=pk, user=request.user)
    
    if request.method == 'POST':
        source.delete()
        messages.success(request, '新闻来源已删除')
        return redirect('news:source_list')
    
    return render(request, 'news/source_delete.html', {'source': source})


@login_required
def source_refresh(request, pk):
    """刷新新闻来源"""
    source = get_object_or_404(NewsSource, pk=pk, user=request.user)
    
    try:
        if source.source_type == 'api':
            count = fetch_news_from_api(source)
            messages.success(request, f'已获取 {count} 篇新闻')
        else:
            messages.info(request, '该来源类型不支持自动刷新')
    except Exception as e:
        messages.error(request, f'刷新失败：{str(e)}')
    
    return redirect('news:article_list')


@login_required
def article_list(request):
    """新闻文章列表"""
    articles = NewsArticle.objects.filter(user=request.user).select_related('source')
    
    # 筛选
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        articles = articles.filter(is_read=False)
    elif filter_type == 'starred':
        articles = articles.filter(is_starred=True)
    
    # 按来源筛选
    source_id = request.GET.get('source')
    if source_id:
        articles = articles.filter(source_id=source_id)
    
    # 按分类筛选
    category = request.GET.get('category')
    if category:
        articles = articles.filter(category=category)
    
    context = {
        'articles': articles[:100],
        'filter_type': filter_type,
        'sources': NewsSource.objects.filter(user=request.user),
        'selected_source': source_id,
        'categories': NewsCategory.objects.filter(user=request.user),
        'selected_category': category,
    }
    return render(request, 'news/article_list.html', context)


@login_required
def article_detail(request, pk):
    """新闻详情"""
    article = get_object_or_404(NewsArticle, pk=pk, user=request.user)
    
    # 标记为已读
    if not article.is_read:
        article.is_read = True
        article.save()
    
    context = {
        'article': article,
    }
    return render(request, 'news/article_detail.html', context)


@require_POST
@login_required
def article_toggle_star(request, pk):
    """切换收藏状态"""
    article = get_object_or_404(NewsArticle, pk=pk, user=request.user)
    article.is_starred = not article.is_starred
    article.save()
    
    return JsonResponse({'success': True, 'is_starred': article.is_starred})


@require_POST
@login_required
def article_toggle_read(request, pk):
    """切换已读状态"""
    article = get_object_or_404(NewsArticle, pk=pk, user=request.user)
    article.is_read = not article.is_read
    article.save()
    
    return JsonResponse({'success': True, 'is_read': article.is_read})


@login_required
def article_delete(request, pk):
    """删除文章"""
    article = get_object_or_404(NewsArticle, pk=pk, user=request.user)
    article.delete()
    messages.success(request, '文章已删除')
    return redirect('news:article_list')


@login_required
def import_from_api(request):
    """从 API 导入新闻"""
    if request.method == 'POST':
        api_url = request.POST.get('api_url')
        api_key = request.POST.get('api_key', '')
        
        if not api_url:
            messages.error(request, '请输入 API 地址')
            return redirect('news:import_from_api')
        
        try:
            # 创建临时来源
            source = NewsSource(
                user=request.user,
                name='API 导入',
                source_type='api',
                api_url=api_url,
                api_key=api_key,
            )
            
            count = fetch_news_from_api(source)
            messages.success(request, f'成功导入 {count} 篇新闻')
            return redirect('news:article_list')
            
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
            return redirect('news:import_from_api')
    
    return render(request, 'news/import_from_api.html')


def fetch_news_from_api(source):
    """从 API 获取新闻"""
    headers = {}
    if source.api_key:
        headers['Authorization'] = f'Bearer {source.api_key}'
    
    response = requests.get(source.api_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    count = 0
    
    # 处理不同格式的 API 响应
    articles = data.get('articles', data.get('data', data.get('results', [])))
    
    for item in articles[:50]:  # 最多 50 篇
        title = item.get('title', '')
        link = item.get('url', item.get('link', ''))
        
        if not title or not link:
            continue
        
        # 解析发布时间
        published_str = item.get('publishedAt', item.get('published_at', item.get('date', '')))
        try:
            if published_str:
                published_at = timezone.parse(published_str)
            else:
                published_at = timezone.now()
        except:
            published_at = timezone.now()
        
        # 创建文章
        article, created = NewsArticle.objects.get_or_create(
            user=source.user,
            link=link,
            defaults={
                'source': source if source.pk else None,
                'title': title[:500],
                'summary': item.get('description', item.get('summary', ''))[:2000],
                'content': item.get('content', '')[:10000],
                'author': item.get('author', '')[:100],
                'category': item.get('category', item.get('section', ''))[:50],
                'image_url': item.get('urlToImage', item.get('image', '')),
                'published_at': published_at,
            }
        )
        
        if created:
            count += 1
    
    return count


# 导入
from django.db import models
from django.utils import dateparse
