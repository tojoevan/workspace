from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from .models import Todo
import json
import re


@login_required
def todo_list(request):
    """待办事项列表"""
    todos = Todo.objects.filter(user=request.user)

    # 筛选
    status = request.GET.get('status', 'all')
    if status != 'all':
        todos = todos.filter(status=status)

    priority = request.GET.get('priority', 'all')
    if priority != 'all':
        todos = todos.filter(priority=priority)

    context = {
        'todos': todos,
        'status_filter': status,
        'priority_filter': priority,
    }
    return render(request, 'todo/todo_list.html', context)


@login_required
def todo_add(request):
    """添加待办"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date')

        if not title:
            messages.error(request, '请输入标题')
            return redirect('todo:todo_add')

        todo = Todo.objects.create(
            user=request.user,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date if due_date else None,
        )
        messages.success(request, '待办已创建')
        return redirect('todo:todo_detail', pk=todo.pk)

    return render(request, 'todo/todo_form.html', {'action': 'add'})


@login_required
@require_POST
def todo_quick_add(request):
    """快速添加待办（AJAX）"""
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()

        if not title:
            return JsonResponse({'success': False, 'error': '标题不能为空'})

        todo = Todo.objects.create(
            user=request.user,
            title=title,
        )

        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'status': todo.get_status_display(),
                'priority': todo.get_priority_display(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def todo_detail(request, pk):
    """待办详情"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    return render(request, 'todo/todo_detail.html', {'todo': todo})


@login_required
def todo_edit(request, pk):
    """编辑待办"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    if request.method == 'POST':
        todo.title = request.POST.get('title', todo.title)
        todo.description = request.POST.get('description', '')
        todo.priority = request.POST.get('priority', 'medium')
        todo.status = request.POST.get('status', 'pending')
        due_date = request.POST.get('due_date')
        todo.due_date = due_date if due_date else None

        if todo.status == 'completed' and not todo.completed_at:
            todo.completed_at = timezone.now()

        todo.save()
        messages.success(request, '待办已更新')
        return redirect('todo:todo_detail', pk=todo.pk)

    return render(request, 'todo/todo_form.html', {'todo': todo, 'action': 'edit'})


@login_required
def todo_delete(request, pk):
    """删除待办"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    if request.method == 'POST':
        todo.delete()
        messages.success(request, '待办已删除')
        return redirect('todo:todo_list')

    return render(request, 'todo/todo_delete.html', {'todo': todo})


@login_required
@require_POST
def todo_toggle_complete(request, pk):
    """切换完成状态"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    if todo.status == 'completed':
        todo.status = 'pending'
        todo.completed_at = None
    else:
        todo.status = 'completed'
        todo.completed_at = timezone.now()

    todo.save()

    return JsonResponse({
        'success': True,
        'status': todo.status,
        'status_display': todo.get_status_display()
    })


@login_required
@require_POST
def todo_toggle_pin(request, pk):
    """切换置顶状态"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    todo.is_pinned = not todo.is_pinned
    todo.save()

    return JsonResponse({
        'success': True,
        'is_pinned': todo.is_pinned
    })


@login_required
def todo_to_bookmark(request, pk):
    """从待办转换为书签"""
    todo = get_object_or_404(Todo, pk=pk, user=request.user)

    # 检查标题或描述是否包含URL
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, todo.title) or re.search(url_pattern, todo.description)

    if match:
        from bookmarks.models import Bookmark
        url = match.group(0)

        # 检查是否已存在
        if Bookmark.objects.filter(user=request.user, url=url).exists():
            messages.warning(request, '该网址已存在于书签中')
            return redirect('todo:todo_detail', pk=pk)

        # 创建书签
        bookmark = Bookmark.objects.create(
            user=request.user,
            title=todo.title.replace(url, '').strip() or url[:50],
            url=url,
            description=todo.description,
            source_type='from_todo',
            related_todo=todo,
            created_by=request.user,
            is_private=True,
        )

        # 关联到待办
        todo.related_bookmark = bookmark
        todo.save()

        messages.success(request, '已转换为书签')
        return redirect('bookmarks:bookmark_detail', pk=bookmark.pk)

    messages.error(request, '未找到有效的网址')
    return redirect('todo:todo_detail', pk=pk)