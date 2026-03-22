#!/bin/bash

# ===================================
# 工作台回滚脚本
# ===================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 显示最近的备份
echo "可用的备份版本："
BACKUP_DIR="/var/backups/workbench"
ls -lt $BACKUP_DIR | head -10

echo ""
read -p "输入要回滚的备份目录名（例如：20260322_143025）: " BACKUP_NAME

TARGET_BACKUP="$BACKUP_DIR/$BACKUP_NAME"

if [ ! -d "$TARGET_BACKUP" ]; then
    echo -e "${RED}备份不存在！${NC}"
    exit 1
fi

log_info "准备回滚到：$TARGET_BACKUP"
read -p "确认回滚？(y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    log_info "取消回滚"
    exit 0
fi

# 停止服务
log_info "停止服务..."
sudo systemctl stop workbench

# 恢复代码
log_info "恢复代码..."
rm -rf /var/www/workbench/*
cp -r $TARGET_BACKUP/* /var/www/workbench/

# 重启服务
log_info "重启服务..."
sudo systemctl start workbench

log_info "✓ 回滚完成！"
log_info "查看状态：sudo systemctl status workbench"
