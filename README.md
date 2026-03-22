# 信息工作台 (Reading Workbench)

一个基于 Django + Tailwind CSS 构建的个人信息管理工作台，集成 RSS 订阅、新闻资讯、笔记系统、待办事项和网址导航等功能。

## 功能特性

### RSS 订阅
- 添加和管理 RSS 订阅源
- 自动获取和更新文章
- 标记已读/未读状态
- 收藏重要文章、稍后阅读
- 从文章快速创建笔记

### 新闻资讯
- 支持 API 导入新闻（NewsAPI、GNews 等）
- 多来源管理
- 分类和标签
- 搜索和筛选
- 收藏和稍后阅读

### 笔记系统
- Markdown 支持
- 标签管理
- 置顶和归档
- 与 RSS/新闻文章关联
- AI 写作助手（总结、改写、扩写、翻译）

### 待办事项
- 优先级管理（低/中/高）
- 状态追踪（待处理/进行中/已完成）
- 截止时间设置
- 置顶功能
- 关联书签

### 网址导航
- 分类管理书签
- 自定义图标和颜色
- 置顶功能
- 访问统计
- 隐私设置
- 从待办事项快速创建书签

### 外部 API
- RESTful API 接口
- API Key 认证
- 新闻推送接口（单个/批量）
- 支持外部应用集成

## 技术栈

- **后端框架**: Django 5.2
- **前端样式**: Tailwind CSS 3.4
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **AI 服务**: OpenAI API（可选）
- **RSS 解析**: feedparser
- **HTTP 客户端**: requests / httpx
- **部署**: Gunicorn

## 项目架构

```
reading-workbench-v3/
├── core/               # 核心应用
│   └── 用户认证、仪表盘、个人设置
├── rss/                # RSS 订阅模块
│   └── RSSFeed、RSSArticle 模型
├── news/               # 新闻资讯模块
│   └── NewsSource、NewsArticle、NewsCategory 模型
├── notes/              # 笔记模块
│   └── Note、UserProfile、AIWritingPrompt、AIWritingHistory 模型
├── todo/               # 待办事项模块
│   └── Todo 模型
├── bookmarks/          # 网址导航模块
│   └── Bookmark、BookmarkCategory 模型
├── api/                # 外部 API 接口
│   └── 新闻推送、API Key 管理
├── workspace/          # 项目配置
│   └── settings、urls、wsgi、asgi
├── templates/          # HTML 模板
│   ├── base.html       # 基础模板
│   ├── core/           # 核心页面模板
│   ├── rss/            # RSS 页面模板
│   ├── news/           # 新闻页面模板
│   ├── notes/          # 笔记页面模板
│   ├── todo/           # 待办页面模板
│   └── bookmarks/      # 书签页面模板
├── static/             # 静态文件
├── manage.py           # Django 管理脚本
├── start.sh            # 启动脚本
└── requirements.txt    # 依赖列表
```

## 数据模型关系

```
User (Django 内置用户模型)
├── UserProfile (用户配置 - OpenAI 设置)
├── RSSFeed → RSSArticle
├── NewsSource → NewsArticle
├── NewsCategory
├── Note (可关联 NewsArticle / RSSArticle)
├── Todo (可关联 Bookmark)
└── BookmarkCategory → Bookmark
```

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd reading-workbench-v3
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI API（可选，用于 AI 写作功能）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或自定义地址
OPENAI_MODEL=gpt-3.5-turbo

# 外部 API 密钥（可选）
EXTERNAL_API_KEYS=1:api-key-1,2:api-key-2
```

### 5. 初始化数据库

```bash
python manage.py migrate
```

### 6. 创建管理员账户

```bash
python manage.py createsuperuser
```

### 7. 启动服务器

```bash
bash start.sh
```

或使用以下命令：

```bash
python manage.py runserver
```

### 8. 访问应用

打开浏览器访问 http://127.0.0.1:8000

## API 接口

### 推送新闻

```bash
POST /api/v1/news/push/
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json

Body:
{
  "title": "新闻标题",
  "link": "https://example.com/article",
  "content": "新闻内容",
  "summary": "摘要",
  "author": "作者",
  "category": "分类",
  "source_name": "来源名称"
}
```

### 批量推送

```bash
POST /api/v1/news/push/batch/
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json

Body:
{
  "articles": [...],
  "source_name": "来源名称"
}
```

### 获取 API Key

```bash
GET /api/v1/key/
（需要登录认证）
```

## 部署说明

详细部署文档请参考 [DEPLOY.md](DEPLOY.md)。

## 许可证

MIT License