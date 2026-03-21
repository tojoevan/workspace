from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Count, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import PasswordChangeForm
from rss.models import RSSFeed, RSSArticle
from news.models import NewsArticle
from notes.models import Note


def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'core/login.html')


def logout_view(request):
    """登出"""
    logout(request)
    return redirect('login')


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
            if email:
                request.user.email = email
                request.user.save()
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

    context = {
        'stats': stats,
        'password_form': password_form,
    }

    return render(request, 'core/user_profile.html', context)
