from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Count, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rss.models import RSSFeed, RSSArticle
from news.models import NewsArticle
from notes.models import Note, UserProfile


def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 首先尝试用用户名登录
        user = authenticate(request, username=username, password=password)

        # 如果用户名登录失败，尝试用别名查找用户
        if user is None:
            try:
                profile = UserProfile.objects.get(alias=username)
                user = authenticate(request, username=profile.user.username, password=password)
            except UserProfile.DoesNotExist:
                pass

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '用户名/别名或密码错误')

    return render(request, 'core/login.html')


def logout_view(request):
    """登出"""
    logout(request)
    return redirect('home')


@ensure_csrf_cookie
def home(request):
    """公开首页 - 无需登录即可查看"""
    # 获取公开的RSS文章（所有用户）
    recent_rss = RSSArticle.objects.filter(
        feed__is_active=True
    ).select_related('feed').order_by('-published_at')[:20]

    # 获取公开的新闻（所有用户）
    recent_news = NewsArticle.objects.all().select_related('source').order_by('-published_at')[:20]

    # 获取公开书签（非隐私的书签）
    from bookmarks.models import Bookmark
    public_bookmarks = Bookmark.objects.filter(
        is_private=False
    ).select_related('user').order_by('-is_pinned', '-created_at')[:15]

    # 如果用户已登录，额外获取其个人数据
    user_todos = []
    user_bookmarks = []
    combined_articles = []
    total_unread = 0

    if request.user.is_authenticated:
        from todo.models import Todo
        user_todos = Todo.objects.filter(
            user=request.user,
            status='pending'
        ).order_by('-is_pinned', '-priority', '-created_at')[:5]

        user_bookmarks = Bookmark.objects.filter(
            user=request.user
        ).order_by('-is_pinned', '-last_visited')[:10]

        # 获取筛选参数
        filter_type = request.GET.get('filter', 'unread')  # unread, starred, read_later, all

        # 构建查询
        rss_articles = RSSArticle.objects.filter(
            feed__user=request.user
        ).select_related('feed')

        news_articles = NewsArticle.objects.filter(
            user=request.user
        ).select_related('source')

        # 应用筛选
        if filter_type == 'starred':
            rss_articles = rss_articles.filter(is_starred=True)
            news_articles = news_articles.filter(is_starred=True)
        elif filter_type == 'read_later':
            rss_articles = rss_articles.filter(is_read_later=True)
            news_articles = news_articles.filter(is_read_later=True)
        elif filter_type == 'unread':
            rss_articles = rss_articles.filter(is_read=False)
            news_articles = news_articles.filter(is_read=False)

        # 计算未读数量
        total_unread = RSSArticle.objects.filter(feed__user=request.user, is_read=False).count()
        total_unread += NewsArticle.objects.filter(user=request.user, is_read=False).count()

        # 合并文章列表
        articles_list = []
        for article in rss_articles[:50]:
            articles_list.append({
                'id': article.id,
                'type': 'rss',
                'title': article.title,
                'link': article.link,
                'source': article.feed.title,
                'published_at': article.published_at,
                'is_read': article.is_read,
                'is_starred': article.is_starred,
                'is_read_later': article.is_read_later,
            })

        for article in news_articles[:50]:
            articles_list.append({
                'id': article.id,
                'type': 'news',
                'title': article.title,
                'link': article.link,
                'source': article.source.name if article.source else '新闻',
                'published_at': article.published_at,
                'is_read': article.is_read,
                'is_starred': article.is_starred,
                'is_read_later': article.is_read_later,
            })

        # 按时间排序
        combined_articles = sorted(articles_list, key=lambda x: x['published_at'], reverse=True)[:12]

    context = {
        'recent_rss': recent_rss,
        'recent_news': recent_news,
        'public_bookmarks': public_bookmarks,
        'user_todos': user_todos,
        'user_bookmarks': user_bookmarks,
        'combined_articles': combined_articles,
        'filter_type': request.GET.get('filter', 'unread') if request.user.is_authenticated else 'unread',
        'total_unread': total_unread,
    }

    return render(request, 'core/home.html', context)


@login_required
@ensure_csrf_cookie
def dashboard(request):
    """仪表盘"""
    # 统计数据
    stats = {
        'rss_feeds': RSSFeed.objects.filter(user=request.user).count(),
        'rss_unread': RSSArticle.objects.filter(feed__user=request.user, is_read=False).count(),
        'news_count': NewsArticle.objects.filter(user=request.user).count(),
        'news_unread': NewsArticle.objects.filter(user=request.user, is_read=False).count(),
        'notes_count': Note.objects.filter(user=request.user).count(),
        'pinned_notes': Note.objects.filter(user=request.user, is_pinned=True).count(),
    }
    
    # 最近的文章
    recent_rss = RSSArticle.objects.filter(
        feed__user=request.user
    ).select_related('feed').order_by('-published_at')[:5]
    
    recent_news = NewsArticle.objects.filter(
        user=request.user
    ).select_related('source').order_by('-published_at')[:5]
    
    # 最近的笔记
    recent_notes = Note.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by('-updated_at')[:6]
    
    # 收藏的文章
    starred_rss = RSSArticle.objects.filter(
        feed__user=request.user,
        is_starred=True
    ).select_related('feed').order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_rss': recent_rss,
        'recent_news': recent_news,
        'recent_notes': recent_notes,
        'starred_rss': starred_rss,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def search(request):
    """全局搜索"""
    query = request.GET.get('q', '')
    
    if query:
        rss_results = RSSArticle.objects.filter(
            feed__user=request.user
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('feed')[:10]
        
        news_results = NewsArticle.objects.filter(
            user=request.user
        ).filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query)
        ).select_related('source')[:10]
        
        note_results = Note.objects.filter(
            user=request.user
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(tags__icontains=query)
        )[:10]
    else:
        rss_results = []
        news_results = []
        note_results = []
    
    context = {
        'query': query,
        'rss_results': rss_results,
        'news_results': news_results,
        'note_results': note_results,
        'total_results': len(rss_results) + len(news_results) + len(note_results),
    }
    
    return render(request, 'core/search.html', context)


@login_required
def api_docs(request):
    """API 文档页面"""
    return render(request, 'core/api_docs.html')


@login_required
def user_profile(request):
    """用户管理页面"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'password':
            # 密码修改
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '密码修改成功！')
                return redirect('user_profile')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        elif form_type == 'profile':
            # 个人信息修改
            email = request.POST.get('email')
            alias = request.POST.get('alias', '').strip()

            if email:
                request.user.email = email
                request.user.save()

            # 更新别名
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            if alias:
                # 检查别名是否已被其他用户使用
                if UserProfile.objects.filter(alias=alias).exclude(user=request.user).exists():
                    messages.error(request, '该别名已被其他用户使用！')
                else:
                    profile.alias = alias
                    profile.save()
                    messages.success(request, '个人信息更新成功！')
                    return redirect('user_profile')
            else:
                profile.alias = None
                profile.save()
                messages.success(request, '个人信息更新成功！')
                return redirect('user_profile')

    # 获取用户统计数据
    stats = {
        'rss_feeds': RSSFeed.objects.filter(user=request.user).count(),
        'rss_articles': RSSArticle.objects.filter(feed__user=request.user).count(),
        'news_articles': NewsArticle.objects.filter(user=request.user).count(),
        'notes': Note.objects.filter(user=request.user).count(),
    }

    password_form = PasswordChangeForm(request.user)

    # 获取用户配置
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'stats': stats,
        'password_form': password_form,
        'profile': profile,
    }

    return render(request, 'core/user_profile.html', context)


@login_required
@require_http_methods(["GET"])
def check_alias(request):
    """检查别名是否可用"""
    alias = request.GET.get('alias', '').strip()

    if not alias:
        return JsonResponse({'available': False, 'message': '别名不能为空'})

    if len(alias) < 2 or len(alias) > 50:
        return JsonResponse({'available': False, 'message': '别名长度需要在2-50个字符之间'})

    # 检查别名是否已被其他用户使用
    exists = UserProfile.objects.filter(alias=alias).exclude(user=request.user).exists()

    if exists:
        return JsonResponse({'available': False, 'message': '该别名已被其他用户使用'})
    else:
        return JsonResponse({'available': True, 'message': '别名可用'})


@login_required
@require_http_methods(["POST"])
def toggle_article_star(request):
    """切换文章收藏状态"""
    article_type = request.POST.get('type')
    article_id = request.POST.get('id')

    if article_type == 'rss':
        try:
            article = RSSArticle.objects.get(id=article_id, feed__user=request.user)
            article.is_starred = not article.is_starred
            article.save()
            return JsonResponse({'success': True, 'is_starred': article.is_starred})
        except RSSArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})
    elif article_type == 'news':
        try:
            article = NewsArticle.objects.get(id=article_id, user=request.user)
            article.is_starred = not article.is_starred
            article.save()
            return JsonResponse({'success': True, 'is_starred': article.is_starred})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})

    return JsonResponse({'success': False, 'error': '无效的文章类型'})


@login_required
@require_http_methods(["POST"])
def toggle_article_read_later(request):
    """切换文章稍后阅读状态"""
    article_type = request.POST.get('type')
    article_id = request.POST.get('id')

    if article_type == 'rss':
        try:
            article = RSSArticle.objects.get(id=article_id, feed__user=request.user)
            article.is_read_later = not article.is_read_later
            article.save()
            return JsonResponse({'success': True, 'is_read_later': article.is_read_later})
        except RSSArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})
    elif article_type == 'news':
        try:
            article = NewsArticle.objects.get(id=article_id, user=request.user)
            article.is_read_later = not article.is_read_later
            article.save()
            return JsonResponse({'success': True, 'is_read_later': article.is_read_later})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})

    return JsonResponse({'success': False, 'error': '无效的文章类型'})


@login_required
@require_http_methods(["POST"])
def mark_article_read(request):
    """标记文章为已读"""
    article_type = request.POST.get('type')
    article_id = request.POST.get('id')

    if article_type == 'rss':
        try:
            article = RSSArticle.objects.get(id=article_id, feed__user=request.user)
            article.is_read = True
            article.save()
            return JsonResponse({'success': True})
        except RSSArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})
    elif article_type == 'news':
        try:
            article = NewsArticle.objects.get(id=article_id, user=request.user)
            article.is_read = True
            article.save()
            return JsonResponse({'success': True})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'error': '文章不存在'})

    return JsonResponse({'success': False, 'error': '无效的文章类型'})


@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """标记当前显示的文章为已读"""
    import json
    try:
        data = json.loads(request.body)
        articles = data.get('articles', [])

        for article in articles:
            article_type = article.get('type')
            article_id = article.get('id')

            if article_type == 'rss':
                RSSArticle.objects.filter(id=article_id, feed__user=request.user).update(is_read=True)
            elif article_type == 'news':
                NewsArticle.objects.filter(id=article_id, user=request.user).update(is_read=True)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
