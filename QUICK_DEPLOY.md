# 工作台 - 快速部署与持续上线指南

## 📋 目录

1. [快速部署流程](#快速部署流程)
2. [代码变更上线流程](#代码变更上线流程)
3. [自动化部署方案](#自动化部署方案)
4. [备份与回滚](#备份与回滚)
5. [监控与日志](#监控与日志)

---

## 🚀 快速部署流程

### 首次部署（生产环境）

#### 1. 服务器准备

```bash
# Ubuntu/Debian 系统
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx postgresql git curl

# 创建应用用户
sudo useradd -m -s /bin/bash workbench
```

#### 2. 数据库配置

```bash
# 创建 PostgreSQL 数据库
sudo -u postgres psql << EOF
CREATE DATABASE workbench;
CREATE USER workbench_user WITH PASSWORD '你的强密码';
ALTER ROLE workbench_user SET client_encoding TO 'utf8';
ALTER ROLE workbench_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE workbench_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE workbench TO workbench_user;
EOF
```

#### 3. 代码部署

```bash
# 切换到应用用户
sudo su - workbench

# 克隆代码
cd /var/www
git clone https://github.com/yourusername/reading-workbench-v3.git workbench
cd workbench

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
nano .env  # 修改配置
```

#### 4. 初始化应用

```bash
# 数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 创建超级用户
python manage.py createsuperuser
```

#### 5. 配置 Systemd 服务

```bash
# 创建服务文件（需要 root 权限）
sudo nano /etc/systemd/system/workbench.service
```

添加以下内容：

```ini
[Unit]
Description=Workbench Gunicorn Service
After=network.target

[Service]
Type=notify
User=workbench
Group=workbench
WorkingDirectory=/var/www/workbench
Environment="PATH=/var/www/workbench/venv/bin"
ExecStart=/var/www/workbench/venv/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          --timeout 120 \
          --access-logfile /var/www/workbench/logs/access.log \
          --error-logfile /var/www/workbench/logs/error.log \
          workspace.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 创建日志目录
sudo mkdir -p /var/www/workbench/logs
sudo chown workbench:workbench /var/www/workbench/logs

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start workbench
sudo systemctl enable workbench
```

#### 6. Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/workbench
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location /static/ {
        alias /var/www/workbench/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/workbench /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 7. SSL 证书（推荐）

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 💻 代码变更上线流程

### 方案一：使用部署脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

**部署脚本自动完成：**
- ✅ 备份当前版本
- ✅ Git 拉取最新代码
- ✅ 更新 Python 依赖
- ✅ 数据库迁移
- ✅ 收集静态文件
- ✅ 重启服务
- ✅ 验证服务状态

### 方案二：手动部署

```bash
cd /var/www/workbench

# 1. 停止服务
sudo systemctl stop workbench

# 2. 更新代码
git pull origin main

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 更新依赖
pip install -r requirements.txt

# 5. 数据库迁移
python manage.py migrate

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 重启服务
sudo systemctl start workbench
```

### 方案三：Git 推送自动部署

#### 服务器配置

```bash
# 创建裸仓库
sudo mkdir -p /var/repo/workbench.git
sudo git init --bare /var/repo/workbench.git
sudo chown -R workbench:workbench /var/repo/workbench.git

# 复制 post-receive hook
cp post-receive-hook.sh /var/repo/workbench.git/hooks/post-receive
chmod +x /var/repo/workbench.git/hooks/post-receive
```

#### 本地配置

```bash
# 添加远程仓库
git remote add production workbench@yourserver:/var/repo/workbench.git

# 推送代码（自动部署）
git push production main
```

---

## 🔄 自动化部署方案

### CI/CD 集成（GitHub Actions 示例）

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy via SSH
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /var/www/workbench
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart workbench
```

### Docker 部署（可选）

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc postgresql-client libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 运行 Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "workspace.wsgi:application"]
```

```bash
# 构建镜像
docker build -t workbench .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/staticfiles:/app/staticfiles \
  --env-file .env \
  --name workbench-app \
  workbench
```

---

## 💾 备份与回滚

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/workbench"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -U workbench_user workbench > $BACKUP_DIR/db_$DATE.sql

# 代码备份
tar -czf $BACKUP_DIR/code_$DATE.tar.gz /var/www/workbench

# 清理旧备份（保留 7 天）
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成：$BACKUP_DIR"
```

**定时备份（crontab）：**

```bash
# 每天凌晨 3 点备份
0 3 * * * /var/www/workbench/backup.sh >> /var/www/workbench/logs/backup.log 2>&1
```

### 快速回滚

```bash
# 使用回滚脚本
chmod +x rollback.sh
./rollback.sh

# 或手动回滚
cd /var/www/workbench
git reset --hard <commit-hash>
sudo systemctl restart workbench
```

---

## 📊 监控与日志

### 实时日志查看

```bash
# 应用日志
tail -f /var/www/workbench/logs/error.log

# Gunicorn 日志
sudo journalctl -u workbench -f

# Nginx日志
tail -f /var/log/nginx/access.log
```

### 服务监控

```bash
# 查看服务状态
sudo systemctl status workbench

# 查看进程
ps aux | grep gunicorn

# 查看端口占用
netstat -tulpn | grep 8000
```

### 健康检查

创建 `health_check.sh`：

```bash
#!/bin/bash

# 检查服务状态
if ! sudo systemctl is-active --quiet workbench; then
    echo "❌ Workbench 服务未运行"
    exit 1
fi

# 检查端口
if ! netstat -tulpn | grep -q ":8000"; then
    echo "❌ 端口 8000 未被监听"
    exit 1
fi

# HTTP 检查
RESPONSE=$(curl -o /dev/null -s -w "%{http_code}" http://127.0.0.1:8000/)
if [ "$RESPONSE" != "200" ]; then
    echo "❌ HTTP 响应异常：$RESPONSE"
    exit 1
fi

echo "✅ 所有检查通过"
```

---

## 🔧 常见问题处理

### 1. 部署失败

```bash
# 查看详细日志
sudo journalctl -u workbench -n 100

# 手动测试启动
cd /var/www/workbench
source venv/bin/activate
python manage.py check
gunicorn --bind 127.0.0.1:8000 workspace.wsgi:application
```

### 2. 数据库迁移错误

```bash
# 回滚迁移
python manage.py migrate <app_name> <previous_migration>

# 或重置迁移（谨慎使用）
python manage.py migrate <app_name> zero
python manage.py migrate
```

### 3. 静态文件问题

```bash
# 重新收集
rm -rf staticfiles/*
python manage.py collectstatic --noinput --clear

# 检查 Nginx 配置
sudo nginx -t
sudo systemctl reload nginx
```

### 4. 性能优化

```bash
# 调整 Gunicorn worker 数量
# 公式：workers = (CPU x 2) + 1
sudo nano /etc/systemd/system/workbench.service
# 修改 --workers 参数
sudo systemctl daemon-reload
sudo systemctl restart workbench
```

---

## 📝 最佳实践

1. **始终在测试环境验证后再部署到生产环境**
2. **使用 Git 分支管理功能开发**
   - `main` - 生产分支
   - `develop` - 开发分支
   - `feature/*` - 功能分支

3. **部署前检查清单：**
   - [ ] 代码审查完成
   - [ ] 测试通过
   - [ ] 数据库迁移脚本就绪
   - [ ] 回滚方案准备
   - [ ] 备份已完成

4. **定期更新：**
   - 每周检查安全更新
   - 每月更新依赖包
   - 每季度审查性能指标

---

## 🎯 快速参考

```bash
# 部署命令汇总
./deploy.sh                    # 执行部署
./rollback.sh                  # 回滚
sudo systemctl restart workbench  # 重启服务
sudo systemctl status workbench   # 查看状态
tail -f logs/error.log         # 查看错误日志
```

---

**技术支持与文档：**
- 详细部署文档：`DEPLOY.md`
- 环境变量配置：`.env.example`
- 启动脚本：`start.sh`
