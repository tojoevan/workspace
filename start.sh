#!/bin/bash

# 信息阅读工作台启动脚本

echo "================================"
echo "  信息阅读工作台启动脚本"
echo "================================"
echo ""

# 设置环境变量
export PATH="/home/kimi/.local/bin:$PATH"

# 检查依赖
echo "检查依赖..."
pip install -q django requests feedparser python-dotenv openai 2>/dev/null

# 执行迁移
echo "执行数据库迁移..."
python manage.py migrate --run-syncdb 2>/dev/null

# 创建默认用户（如果不存在）
echo "检查默认用户..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reading_workbench.settings')
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('创建默认用户: admin / admin123')
else:
    print('默认用户已存在')
" 2>/dev/null

echo ""
echo "================================"
echo "  启动服务器"
echo "================================"
echo ""
echo "访问地址: http://127.0.0.1:8000"
echo ""
echo "默认账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python manage.py runserver 127.0.0.1:8000
