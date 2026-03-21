# 信息工作台

一个基于 Django + Tailwind CSS 构建的信息工作台，支持 RSS 订阅、API 新闻导入和 AI 写作笔记功能。

## 功能特性

### RSS 订阅
- 添加和管理 RSS 订阅源
- 自动获取和更新文章
- 标记已读/未读状态
- 收藏重要文章
- 从文章快速创建笔记

### 新闻资讯
- 支持 API 导入新闻（NewsAPI、GNews 等）
- 多来源管理
- 分类和标签
- 搜索和筛选

### 笔记系统
- Markdown 支持
- 标签管理
- 置顶和归档
- 与 RSS/新闻文章关联

### AI 写作助手
- 文章总结
- 内容改写
- 扩写和润色
- 多语言翻译
- 自定义提示词

## 技术栈

- **后端**: Django 6.0+
- **前端**: Tailwind CSS 3.4+
- **数据库**: SQLite（默认）
- **AI**: OpenAI GPT-3.5

## 快速开始

### 1. 安装依赖

```bash
pip install django requests feedparser python-dotenv openai
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
SECRET_KEY=your-secret-key
DEBUG=True
OPENAI_API_KEY=your-openai-api-key  # 可选，用于 AI 写作功能
```

### 3. 启动服务器

```bash
bash start.sh
```

或使用以下命令：

```bash
python manage.py migrate
python manage.py runserver
```

### 4. 访问应用

打开浏览器访问 http://127.0.0.1:8000

默认账号：
- 用户名: `admin`
- 密码: `admin123`

## 使用指南

### 添加 RSS 订阅

1. 点击侧边栏 "RSS 订阅"
2. 点击 "添加订阅源"
3. 输入 RSS 链接（如：https://sspai.com/feed）
4. 系统自动获取文章

### 导入新闻

1. 点击侧边栏 "新闻资讯"
2. 点击 "从 API 导入"
3. 输入 API 地址和密钥
4. 系统自动获取新闻

### 使用 AI 写作

1. 打开任意笔记
2. 点击 "AI 写作" 按钮
3. 选择操作（总结、改写、扩写、翻译）
4. 查看 AI 生成结果并追加或替换到笔记

## 项目结构

```
reading-workbench/
├── core/               # 核心应用（用户认证、仪表盘）
├── rss/                # RSS 订阅功能
├── news/               # 新闻资讯功能
├── notes/              # 笔记和 AI 写作功能
├── templates/          # HTML 模板
├── static/             # 静态文件
├── manage.py           # Django 管理脚本
└── start.sh            # 启动脚本
```

## 截图

- 仪表盘：统计信息、最新文章、最近笔记
- RSS 订阅：订阅源管理、文章列表
- 新闻资讯：API 导入、文章阅读
- 笔记系统：Markdown 编辑、AI 写作

## 许可证

MIT License
