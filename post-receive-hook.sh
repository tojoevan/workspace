#!/bin/bash

# ===================================
# Git Post-receive Hook - 自动部署
# ===================================
# 使用方法：
# 1. 在服务器上创建裸仓库：git init --bare /var/repo/workbench.git
# 2. 将此脚本保存为 /var/repo/workbench.git/hooks/post-receive
# 3. 添加执行权限：chmod +x /var/repo/workbench.git/hooks/post-receive
# 4. 本地添加远程仓库：git remote add production user@server:/var/repo/workbench.git
# 5. 推送代码：git push production main

set -e

APP_DIR="/var/www/workbench"
VENV_DIR="$APP_DIR/venv"

echo "🚀 开始自动部署..."

cd $APP_DIR

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source $VENV_DIR/bin/activate

# 更新依赖
pip install -r requirements.txt -q

# 数据库迁移
python manage.py migrate --noinput

# 收集静态文件
python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart workbench

echo "✅ 部署完成！"
