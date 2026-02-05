import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.conf import settings
from .models import Note, AIWritingPrompt, AIWritingHistory


@login_required
@ensure_csrf_cookie
def note_list(request):
    """笔记列表"""
    notes = Note.objects.filter(user=request.user)
    
    # 筛选
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'pinned':
        notes = notes.filter(is_pinned=True)
    elif filter_type == 'archived':
        notes = notes.filter(is_archived=True)
    
    # 标签筛选
    tag = request.GET.get('tag')
    if tag:
        notes = notes.filter(tags__icontains=tag)
    
    # 搜索
    search = request.GET.get('search')
    if search:
        notes = notes.filter(title__icontains=search) | notes.filter(content__icontains=search)
    
    # 获取所有标签
    all_tags = set()
    for note in Note.objects.filter(user=request.user):
        all_tags.update(note.get_tags_list())
    
    context = {
        'notes': notes,
        'filter_type': filter_type,
        'selected_tag': tag,
        'all_tags': sorted(all_tags),
        'search': search,
    }
    return render(request, 'notes/note_list.html', context)


@login_required
def note_detail(request, pk):
    """笔记详情"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    context = {
        'note': note,
        'ai_history': note.ai_history.all()[:5],
    }
    return render(request, 'notes/note_detail.html', context)


@login_required
def note_add(request):
    """添加笔记"""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        note_type = request.POST.get('note_type', 'markdown')
        tags = request.POST.get('tags', '')
        
        if not title:
            messages.error(request, '请输入标题')
            return redirect('notes:note_add')
        
        note = Note.objects.create(
            user=request.user,
            title=title,
            content=content,
            note_type=note_type,
            tags=tags,
        )
        
        messages.success(request, '笔记已创建')
        return redirect('notes:note_detail', pk=note.pk)
    
    return render(request, 'notes/note_form.html', {'action': 'add'})


@login_required
def note_edit(request, pk):
    """编辑笔记"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note.title = request.POST.get('title', note.title)
        note.content = request.POST.get('content', note.content)
        note.note_type = request.POST.get('note_type', note.note_type)
        note.tags = request.POST.get('tags', note.tags)
        note.save()
        
        messages.success(request, '笔记已更新')
        return redirect('notes:note_detail', pk=note.pk)
    
    context = {
        'note': note,
        'action': 'edit',
    }
    return render(request, 'notes/note_form.html', context)


@login_required
def note_delete(request, pk):
    """删除笔记"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, '笔记已删除')
        return redirect('notes:note_list')
    
    return render(request, 'notes/note_delete.html', {'note': note})


@require_POST
@login_required
def note_toggle_pin(request, pk):
    """切换置顶状态"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.is_pinned = not note.is_pinned
    note.save()
    
    return JsonResponse({'success': True, 'is_pinned': note.is_pinned})


@require_POST
@login_required
def note_toggle_archive(request, pk):
    """切换归档状态"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.is_archived = not note.is_archived
    note.save()
    
    return JsonResponse({'success': True, 'is_archived': note.is_archived})


@login_required
def ai_write(request, pk):
    """AI 写作助手"""
    from .models import UserProfile

    note = get_object_or_404(Note, pk=pk, user=request.user)

    # 获取提示词模板
    prompts = AIWritingPrompt.objects.filter(
        models.Q(user=request.user) | models.Q(is_default=True)
    ).order_by('-is_default', '-created_at')

    # 获取用户配置
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    api_key = profile.openai_api_key or settings.OPENAI_API_KEY
    base_url = profile.openai_base_url or settings.OPENAI_BASE_URL
    model = profile.openai_model or settings.OPENAI_MODEL
    
    if request.method == 'POST':
        action = request.POST.get('action')
        prompt_text = request.POST.get('prompt', '')
        selected_text = request.POST.get('selected_text', '')
        
        if not api_key:
            return JsonResponse({'success': False, 'error': '请先配置 OpenAI API 密钥', 'need_config': True})
        
        try:
            import openai
            
            # 创建客户端，支持自定义 base_url
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url if base_url else None
            )
            
            # 构建提示词
            if action == 'summarize':
                system_prompt = "你是一个专业的内容总结助手。请总结以下内容，提取关键要点："
                user_content = selected_text or note.content
            elif action == 'rewrite':
                system_prompt = "你是一个专业的写作助手。请改写以下内容，使其更加流畅和专业："
                user_content = selected_text or note.content
            elif action == 'expand':
                system_prompt = "你是一个专业的写作助手。请扩展以下内容，增加更多细节和深度："
                user_content = selected_text or note.content
            elif action == 'translate':
                target_lang = request.POST.get('target_lang', '中文')
                system_prompt = f"请将以下内容翻译成{target_lang}："
                user_content = selected_text or note.content
            else:
                system_prompt = prompt_text or "你是一个专业的写作助手。"
                user_content = selected_text or note.content
            
            # 调用 API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            
            result = response.choices[0].message.content
            
            # 保存历史
            AIWritingHistory.objects.create(
                user=request.user,
                note=note,
                prompt=system_prompt,
                input_content=user_content,
                output_content=result,
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )
            
            # 更新笔记内容
            if request.POST.get('replace_content') == 'on':
                if selected_text:
                    note.content = note.content.replace(selected_text, result)
                else:
                    note.content = result
                note.save()
            
            return JsonResponse({
                'success': True,
                'result': result,
                'tokens_used': response.usage.total_tokens if response.usage else 0,
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {
        'note': note,
        'prompts': prompts,
        'ai_history': note.ai_history.all()[:10],
        'api_configured': bool(api_key),
        'model': model,
    }
    return render(request, 'notes/ai_write.html', context)


@login_required
def ai_prompt_list(request):
    """AI 提示词模板列表"""
    prompts = AIWritingPrompt.objects.filter(
        models.Q(user=request.user) | models.Q(is_default=True)
    ).order_by('-is_default', '-created_at')
    
    context = {
        'prompts': prompts,
    }
    return render(request, 'notes/ai_prompt_list.html', context)


@login_required
def ai_prompt_add(request):
    """添加 AI 提示词模板"""
    if request.method == 'POST':
        name = request.POST.get('name')
        prompt_type = request.POST.get('prompt_type', 'custom')
        prompt_template = request.POST.get('prompt_template')
        
        if not name or not prompt_template:
            messages.error(request, '请填写完整信息')
            return redirect('notes:ai_prompt_add')
        
        AIWritingPrompt.objects.create(
            user=request.user,
            name=name,
            prompt_type=prompt_type,
            prompt_template=prompt_template,
        )
        
        messages.success(request, '提示词模板已创建')
        return redirect('notes:ai_prompt_list')
    
    return render(request, 'notes/ai_prompt_form.html')


@login_required
def quick_note_from_article(request):
    """从文章快速创建笔记"""
    article_type = request.GET.get('type')
    article_id = request.GET.get('id')
    
    initial_title = ''
    initial_content = ''
    
    if article_type == 'rss' and article_id:
        from rss.models import RSSArticle
        article = get_object_or_404(RSSArticle, pk=article_id, feed__user=request.user)
        initial_title = f"笔记：{article.title}"
        initial_content = f"原文：{article.title}\n链接：{article.link}\n\n---\n\n"
    elif article_type == 'news' and article_id:
        article = get_object_or_404(NewsArticle, pk=article_id, user=request.user)
        initial_title = f"笔记：{article.title}"
        initial_content = f"原文：{article.title}\n链接：{article.link}\n\n---\n\n"
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        tags = request.POST.get('tags', '')
        
        note = Note.objects.create(
            user=request.user,
            title=title,
            content=content,
            tags=tags,
        )
        
        # 关联文章
        if article_type == 'rss' and article_id:
            from rss.models import RSSArticle
            article = get_object_or_404(RSSArticle, pk=article_id, feed__user=request.user)
            note.related_rss = article
            note.save()
        elif article_type == 'news' and article_id:
            article = get_object_or_404(NewsArticle, pk=article_id, user=request.user)
            note.related_article = article
            note.save()
        
        messages.success(request, '笔记已创建')
        return redirect('notes:note_detail', pk=note.pk)
    
    context = {
        'initial_title': initial_title,
        'initial_content': initial_content,
    }
    return render(request, 'notes/quick_note.html', context)


# 导入
from django.db import models
from news.models import NewsArticle


@login_required
def ai_settings(request):
    """AI 配置页面"""
    from .models import UserProfile

    # 获取或创建用户配置
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.openai_api_key = request.POST.get('api_key', '').strip()
        profile.openai_base_url = request.POST.get('base_url', '').strip()
        profile.openai_model = request.POST.get('model', '').strip()
        profile.save()

        messages.success(request, 'AI 配置已保存')
        return redirect('notes:ai_settings')

    # 获取当前配置
    context = {
        'api_key': profile.openai_api_key or settings.OPENAI_API_KEY,
        'base_url': profile.openai_base_url or settings.OPENAI_BASE_URL,
        'model': profile.openai_model or settings.OPENAI_MODEL,
        'default_api_key': settings.OPENAI_API_KEY,
        'default_base_url': settings.OPENAI_BASE_URL,
        'default_model': settings.OPENAI_MODEL,
    }
    return render(request, 'notes/ai_settings.html', context)


@login_required
@csrf_exempt
@require_POST
def ai_chat(request):
    """AI 聊天接口"""
    from .models import UserProfile

    profile, created = UserProfile.objects.get_or_create(user=request.user)
    api_key = profile.openai_api_key or settings.OPENAI_API_KEY
    base_url = profile.openai_base_url or settings.OPENAI_BASE_URL
    model = profile.openai_model or settings.OPENAI_MODEL

    if not api_key:
        return JsonResponse({'success': False, 'error': '请先配置 AI 密钥'})

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()

        if not message:
            return JsonResponse({'success': False, 'error': '消息不能为空'})

        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url if base_url else None)

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            max_tokens=1000,
            temperature=0.7,
        )

        return JsonResponse({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
