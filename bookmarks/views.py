from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Bookmark, BookmarkCategory
import json


def bookmark_public(request):
    """公开书签页面（无需登录）"""
    bookmarks = Bookmark.objects.filter(is_private=False).select_related('user', 'category')

    # 分类筛选
    category_id = request.GET.get('category')
    if category_id:
        bookmarks = bookmarks.filter(category_id=category_id)

    # 搜索
    search = request.GET.get('search')
    if search:
        bookmarks = bookmarks.filter(title__icontains=search) | bookmarks.filter(url__icontains=search)

    # 排序
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'title', '-title', '-visit_count', 'visit_count', '-last_visited', 'last_visited']
    if sort in valid_sorts:
        bookmarks = bookmarks.order_by('-is_pinned', sort)
    else:
        bookmarks = bookmarks.order_by('-is_pinned', '-created_at')

    # 获取所有有公开书签的分类
    categories = BookmarkCategory.objects.filter(
        pk__in=bookmarks.values_list('category_id', flat=True).distinct()
    )

    context = {
        'bookmarks': bookmarks,
        'categories': categories,
        'selected_category': category_id,
        'search': search,
        'sort': sort,
    }
    return render(request, 'bookmarks/bookmark_public.html', context)


@login_required
def bookmark_list(request):
    """书签列表（仅显示自己的）"""
    bookmarks = Bookmark.objects.filter(user=request.user)

    # 分类筛选
    category_id = request.GET.get('category')
    if category_id:
        bookmarks = bookmarks.filter(category_id=category_id)

    # 搜索
    search = request.GET.get('search')
    if search:
        bookmarks = bookmarks.filter(title__icontains=search) | bookmarks.filter(url__icontains=search)

    # 排序
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'title', '-title', '-visit_count', 'visit_count', '-last_visited', 'last_visited', '-is_pinned']
    if sort in valid_sorts:
        bookmarks = bookmarks.order_by(sort)
    else:
        bookmarks = bookmarks.order_by('-is_pinned', '-created_at')

    categories = BookmarkCategory.objects.filter(user=request.user)

    context = {
        'bookmarks': bookmarks,
        'categories': categories,
        'selected_category': category_id,
        'search': search,
        'sort': sort,
    }
    return render(request, 'bookmarks/bookmark_list.html', context)


@login_required
def bookmark_add(request):
    """添加书签"""
    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        if not url:
            messages.error(request, '请输入网址')
            return redirect('bookmarks:bookmark_add')

        # 检查是否已存在
        if Bookmark.objects.filter(user=request.user, url=url).exists():
            messages.warning(request, '该网址已存在')
            return redirect('bookmarks:bookmark_list')

        is_private = request.POST.get('is_private') == 'on'

        bookmark = Bookmark.objects.create(
            user=request.user,
            title=title or url[:50],
            url=url,
            description=description,
            category_id=category_id if category_id else None,
            is_private=is_private,
            created_by=request.user,
        )

        messages.success(request, '书签已添加')
        return redirect('bookmarks:bookmark_detail', pk=bookmark.pk)

    categories = BookmarkCategory.objects.filter(user=request.user)
    return render(request, 'bookmarks/bookmark_form.html', {'action': 'add', 'categories': categories})


@login_required
@require_POST
def bookmark_quick_add(request):
    """快速添加书签（AJAX）"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not url:
            return JsonResponse({'success': False, 'error': '网址不能为空'})

        # 检查是否已存在
        if Bookmark.objects.filter(user=request.user, url=url).exists():
            return JsonResponse({'success': False, 'error': '该网址已存在'})

        bookmark = Bookmark.objects.create(
            user=request.user,
            title=title or url[:50],
            url=url,
            description=description,
            is_private=True,  # 默认隐私
            created_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'bookmark': {
                'id': bookmark.id,
                'title': bookmark.title,
                'url': bookmark.url,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def bookmark_detail(request, pk):
    """书签详情"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    return render(request, 'bookmarks/bookmark_detail.html', {'bookmark': bookmark})


@login_required
def bookmark_edit(request, pk):
    """编辑书签"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)

    if request.method == 'POST':
        bookmark.title = request.POST.get('title', bookmark.title)
        bookmark.url = request.POST.get('url', bookmark.url)
        bookmark.description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        bookmark.category_id = category_id if category_id else None
        bookmark.is_private = request.POST.get('is_private') == 'on'
        bookmark.save()

        messages.success(request, '书签已更新')
        return redirect('bookmarks:bookmark_detail', pk=bookmark.pk)

    categories = BookmarkCategory.objects.filter(user=request.user)
    return render(request, 'bookmarks/bookmark_form.html', {'bookmark': bookmark, 'action': 'edit', 'categories': categories})


@login_required
def bookmark_delete(request, pk):
    """删除书签"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)

    if request.method == 'POST':
        bookmark.delete()
        messages.success(request, '书签已删除')
        return redirect('bookmarks:bookmark_list')

    return render(request, 'bookmarks/bookmark_delete.html', {'bookmark': bookmark})


@login_required
@require_POST
def bookmark_toggle_pin(request, pk):
    """切换置顶状态"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    bookmark.is_pinned = not bookmark.is_pinned
    bookmark.save()

    return JsonResponse({
        'success': True,
        'is_pinned': bookmark.is_pinned
    })


@login_required
@require_POST
def bookmark_toggle_privacy(request, pk):
    """切换隐私状态"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    bookmark.is_private = not bookmark.is_private
    bookmark.save()

    return JsonResponse({
        'success': True,
        'is_private': bookmark.is_private
    })


@login_required
@require_POST
def bookmark_visit(request, pk):
    """记录书签访问"""
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    bookmark.visit_count += 1
    bookmark.last_visited = timezone.now()
    bookmark.save()

    return JsonResponse({'success': True})


@login_required
def category_list(request):
    """分类列表"""
    categories = BookmarkCategory.objects.filter(user=request.user)
    return render(request, 'bookmarks/category_list.html', {'categories': categories})


@login_required
def category_add(request):
    """添加分类"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', 'fas fa-folder')
        color = request.POST.get('color', '#3B82F6')

        if not name:
            messages.error(request, '请输入分类名称')
            return redirect('bookmarks:category_add')

        if BookmarkCategory.objects.filter(user=request.user, name=name).exists():
            messages.warning(request, '该分类已存在')
            return redirect('bookmarks:category_list')

        BookmarkCategory.objects.create(
            user=request.user,
            name=name,
            icon=icon,
            color=color,
        )

        messages.success(request, '分类已添加')
        return redirect('bookmarks:category_list')

    return render(request, 'bookmarks/category_form.html')