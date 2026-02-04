"""
API 接口 - 允许外部应用推送新闻至工作台
"""
import json
import hashlib
import hmac
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from news.models import NewsArticle, NewsSource


API_KEY_STORE = {}


def init_api_keys():
    """初始化 API 密钥存储"""
    global API_KEY_STORE
    # 从环境变量或数据库加载 API 密钥
    # 格式: user_id:api_key
    api_keys_str = getattr(settings, 'EXTERNAL_API_KEYS', '')
    if api_keys_str:
        for key_pair in api_keys_str.split(','):
            if ':' in key_pair:
                user_id, api_key = key_pair.strip().split(':', 1)
                API_KEY_STORE[api_key.strip()] = int(user_id.strip())


# 初始化 API 密钥
init_api_keys()


def verify_api_key(request):
    """验证 API 密钥"""
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return None, {'error': 'Missing API key', 'code': 401}
    
    user_id = API_KEY_STORE.get(api_key)
    if not user_id:
        return None, {'error': 'Invalid API key', 'code': 403}
    
    try:
        user = User.objects.get(id=user_id)
        return user, None
    except User.DoesNotExist:
        return None, {'error': 'User not found', 'code': 404}


@csrf_exempt
@require_http_methods(["POST"])
def push_news(request):
    """
    推送新闻接口
    
    POST /api/v1/news/push/
    Headers:
        X-API-Key: your-api-key
        Content-Type: application/json
    
    Body:
    {
        "title": "新闻标题",
        "content": "新闻内容",
        "summary": "摘要（可选）",
        "link": "原文链接",
        "author": "作者（可选）",
        "category": "分类（可选）",
        "image_url": "图片链接（可选）",
        "published_at": "发布时间 ISO 格式（可选）",
        "source_name": "来源名称（可选）"
    }
    """
    user, error = verify_api_key(request)
    if error:
        return JsonResponse(error, status=error['code'])
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON', 'code': 400}, status=400)
    
    # 验证必填字段
    title = data.get('title', '').strip()
    link = data.get('link', '').strip()
    
    if not title:
        return JsonResponse({'error': 'Title is required', 'code': 400}, status=400)
    
    if not link:
        return JsonResponse({'error': 'Link is required', 'code': 400}, status=400)
    
    # 获取或创建来源
    source_name = data.get('source_name', 'API 推送')
    source, _ = NewsSource.objects.get_or_create(
        user=user,
        name=source_name,
        defaults={
            'source_type': 'api',
            'is_active': True,
        }
    )
    
    # 解析发布时间
    published_at_str = data.get('published_at')
    if published_at_str:
        try:
            published_at = timezone.parse(published_at_str)
        except:
            published_at = timezone.now()
    else:
        published_at = timezone.now()
    
    # 创建或更新文章
    article, created = NewsArticle.objects.update_or_create(
        user=user,
        link=link,
        defaults={
            'source': source,
            'title': title[:500],
            'content': data.get('content', '')[:10000],
            'summary': data.get('summary', '')[:2000],
            'author': data.get('author', '')[:100],
            'category': data.get('category', '')[:50],
            'image_url': data.get('image_url', ''),
            'published_at': published_at,
            'is_read': False,
        }
    )
    
    return JsonResponse({
        'success': True,
        'message': 'News article pushed successfully',
        'data': {
            'id': article.id,
            'title': article.title,
            'created': created,
            'published_at': article.published_at.isoformat(),
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def push_news_batch(request):
    """
    批量推送新闻接口
    
    POST /api/v1/news/push/batch/
    Headers:
        X-API-Key: your-api-key
        Content-Type: application/json
    
    Body:
    {
        "articles": [
            {
                "title": "新闻标题1",
                "link": "链接1",
                ...
            },
            {
                "title": "新闻标题2",
                "link": "链接2",
                ...
            }
        ],
        "source_name": "来源名称（可选，应用于所有文章）"
    }
    """
    user, error = verify_api_key(request)
    if error:
        return JsonResponse(error, status=error['code'])
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON', 'code': 400}, status=400)
    
    articles_data = data.get('articles', [])
    if not isinstance(articles_data, list):
        return JsonResponse({'error': 'articles must be an array', 'code': 400}, status=400)
    
    default_source_name = data.get('source_name', 'API 批量推送')
    
    # 获取或创建来源
    source, _ = NewsSource.objects.get_or_create(
        user=user,
        name=default_source_name,
        defaults={
            'source_type': 'api',
            'is_active': True,
        }
    )
    
    results = []
    success_count = 0
    error_count = 0
    
    for idx, article_data in enumerate(articles_data):
        title = article_data.get('title', '').strip()
        link = article_data.get('link', '').strip()
        
        if not title or not link:
            results.append({
                'index': idx,
                'success': False,
                'error': 'Missing title or link'
            })
            error_count += 1
            continue
        
        try:
            # 解析发布时间
            published_at_str = article_data.get('published_at')
            if published_at_str:
                try:
                    published_at = timezone.parse(published_at_str)
                except:
                    published_at = timezone.now()
            else:
                published_at = timezone.now()
            
            article, created = NewsArticle.objects.update_or_create(
                user=user,
                link=link,
                defaults={
                    'source': source,
                    'title': title[:500],
                    'content': article_data.get('content', '')[:10000],
                    'summary': article_data.get('summary', '')[:2000],
                    'author': article_data.get('author', '')[:100],
                    'category': article_data.get('category', '')[:50],
                    'image_url': article_data.get('image_url', ''),
                    'published_at': published_at,
                    'is_read': False,
                }
            )
            
            results.append({
                'index': idx,
                'success': True,
                'id': article.id,
                'created': created,
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                'index': idx,
                'success': False,
                'error': str(e)
            })
            error_count += 1
    
    return JsonResponse({
        'success': True,
        'message': f'Batch push completed: {success_count} succeeded, {error_count} failed',
        'data': {
            'total': len(articles_data),
            'success': success_count,
            'failed': error_count,
            'results': results,
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
def api_status(request):
    """
    API 状态检查接口
    
    GET /api/v1/status/
    """
    return JsonResponse({
        'status': 'ok',
        'version': '1.0',
        'timestamp': timezone.now().isoformat(),
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_api_key(request):
    """
    获取 API 密钥（需要登录）
    
    GET /api/v1/key/
    """
    from django.contrib.auth.decorators import login_required
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required', 'code': 401}, status=401)
    
    # 生成或获取用户的 API 密钥
    user = request.user
    api_key = generate_api_key(user)
    
    # 存储密钥
    API_KEY_STORE[api_key] = user.id
    
    return JsonResponse({
        'success': True,
        'data': {
            'api_key': api_key,
            'user_id': user.id,
            'username': user.username,
        }
    })


def generate_api_key(user):
    """生成 API 密钥"""
    import secrets
    import string
    
    # 生成随机密钥
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # 添加用户标识
    key = f"rb_{user.id}_{random_part}"
    
    return key
