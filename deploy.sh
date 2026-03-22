#!/bin/bash

# ===================================
# 工作台快速部署脚本
# ===================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置项
APP_DIR="/var/www/workbench"
VENV_DIR="$APP_DIR/venv"
LOG_FILE="$APP_DIR/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# 开始部署
log_info "=========================================="
log_info "  开始部署工作台应用"
log_info "=========================================="

cd $APP_DIR

# 1. 备份当前版本
log_info "备份当前版本..."
BACKUP_DIR="/var/backups/workbench/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r $APP_DIR $BACKUP_DIR/ 2>/dev/null || log_warn "跳过备份（首次部署）"

# 2. 更新代码
log_info "更新代码..."
git pull origin main  # 或你的分支名

# 3. 激活虚拟环境
log_info "激活虚拟环境..."
source $VENV_DIR/bin/activate

# 4. 更新依赖
log_info "更新 Python 依赖..."
pip install -r requirements.txt -q

# 5. 数据库迁移
log_info "执行数据库迁移..."
python manage.py migrate --noinput

# 6. 收集静态文件
log_info "收集静态文件..."
python manage.py collectstatic --noinput

# 7. 重启服务
log_info "重启 Gunicorn 服务..."
sudo systemctl restart workbench

# 8. 验证服务状态
sleep 2
if sudo systemctl is-active --quiet workbench; then
    log_info "✓ 部署成功！服务运行正常"
else
    log_error "✗ 部署失败！服务未正常运行"
    log_info "查看日志：sudo journalctl -u workbench -n 50"
    exit 1
fi

log_info "=========================================="
log_info "  部署完成！"
log_info "=========================================="
