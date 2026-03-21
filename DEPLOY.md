# 工作台部署指南

本文档详细说明如何将工作台应用部署到生产环境。

## 目录

1. [环境要求](#环境要求)
2. [服务器准备](#服务器准备)
3. [数据库迁移](#数据库迁移)
4. [应用部署](#应用部署)
5. [Nginx配置](#nginx配置)
6. [SSL证书配置](#ssl证书配置)
7. [进程管理](#进程管理)
8. [定时任务](#定时任务)
9. [常见问题](#常见问题)

---

## 环境要求

- **操作系统**: Ubuntu 22.04+ / CentOS 7+ / Debian 11+
- **Python**: 3.11+
- **数据库**: SQLite（开发）/ PostgreSQL（生产推荐）
- **Web服务器**: Nginx
- **应用服务器**: Gunicorn

---

## 服务器准备

### 1. 更新系统

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS
sudo yum update -y
```

### 2. 安装依赖

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# CentOS
sudo yum install -y python3 python3-pip nginx postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3. 创建应用用户

```bash
sudo useradd -m -s /bin/bash workbench
sudo passwd workbench
```

---

## 数据库迁移

### 方案一：使用SQLite（简单部署）

SQLite数据库文件 `db.sqlite3` 可以直接复制到生产服务器。

```bash
# 在本地导出数据（可选，用于备份）
cp db.sqlite3 db_backup_$(date +%Y%m%d).sqlite3

# 上传到服务器
scp db.sqlite3 user@server:/var/www/workbench/
```

### 方案二：迁移到PostgreSQL（推荐生产环境）

#### 1. 创建PostgreSQL数据库

```bash
# 切换到postgres用户
sudo -u postgres psql

# 在psql中执行
CREATE DATABASE workbench;
CREATE USER workbench_user WITH PASSWORD 'your_strong_password';
ALTER ROLE workbench_user SET client_encoding TO 'utf8';
ALTER ROLE workbench_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE workbench_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE workbench TO workbench_user;
\q
```

#### 2. 修改settings.py使用PostgreSQL

在 `workspace/settings.py` 中修改数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'workbench',
        'USER': 'workbench_user',
        'PASSWORD': 'your_strong_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 3. 迁移数据

```bash
# 安装PostgreSQL客户端依赖
pip install psycopg2-binary

# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 从SQLite导入数据到PostgreSQL（使用dumpdata）
# 先在本地SQLite环境执行：
python manage.py dumpdata > data_backup.json

# 然后在新PostgreSQL环境执行：
python manage.py loaddata data_backup.json

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic --noinput
```

---

## 应用部署

### 1. 上传代码

```bash
# 创建应用目录
sudo mkdir -p /var/www/workbench
sudo chown workbench:workbench /var/www/workbench

# 上传代码（方式一：scp）
scp -r ./* user@server:/var/www/workbench/

# 上传代码（方式二：git clone）
cd /var/www/workbench
git clone https://github.com/yourusername/reading-workbench-v3.git .
```

### 2. 创建虚拟环境

```bash
cd /var/www/workbench
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 创建环境变量文件

```bash
# 创建 .env 文件
cat > /var/www/workbench/.env << 'EOF'
# 安全密钥（生产环境必须修改！）
SECRET_KEY=your-production-secret-key-change-this

# 调试模式（生产环境设为False）
DEBUG=False

# 允许的主机
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server-ip

# 数据库配置（使用PostgreSQL时）
DB_NAME=workbench
DB_USER=workbench_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost
DB_PORT=5432

# OpenAI API配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 外部API密钥（格式: "user_id:api_key"）
EXTERNAL_API_KEYS=
EOF

# 设置权限
chmod 600 /var/www/workbench/.env
```

### 4. 修改settings.py读取环境变量

更新 `workspace/settings.py`：

```python
import os
from dotenv import load_dotenv

load_dotenv()

# 安全设置
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# CSRF信任来源
CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host
] + [f'http://{host}' for host in ALLOWED_HOSTS if host]

# 数据库配置（支持PostgreSQL）
if os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
```

### 5. 初始化应用

```bash
cd /var/www/workbench
source venv/bin/activate

# 收集静态文件
python manage.py collectstatic --noinput

# 创建超级用户（如果还没有）
python manage.py createsuperuser
```

---

## Nginx配置

### 1. 创建Nginx配置

```bash
sudo nano /etc/nginx/sites-available/workbench
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 静态文件
    location /static/ {
        alias /var/www/workbench/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /var/www/workbench/media/;
        expires 7d;
    }

    # 代理到Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_read_timeout 300;
    }
}
```

### 2. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/workbench /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL证书配置

### 使用Let's Encrypt免费证书

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期测试
sudo certbot renew --dry-run
```

Certbot会自动修改Nginx配置，添加SSL相关设置。

---

## 进程管理

### 使用Systemd管理Gunicorn

#### 1. 创建服务文件

```bash
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

[Install]
WantedBy=multi-user.target
```

#### 2. 创建日志目录

```bash
sudo mkdir -p /var/www/workbench/logs
sudo chown workbench:workbench /var/www/workbench/logs
```

#### 3. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl start workbench
sudo systemctl enable workbench

# 查看状态
sudo systemctl status workbench
```

---

## 定时任务

### RSS更新定时任务

```bash
sudo crontab -e
```

添加以下内容：

```cron
# 每30分钟更新RSS
*/30 * * * * cd /var/www/workbench && /var/www/workbench/venv/bin/python manage.py update_rss >> /var/www/workbench/logs/cron.log 2>&1

# 每天凌晨清理过期数据
0 2 * * * cd /var/www/workbench && /var/www/workbench/venv/bin/python manage.py cleanup_old_data >> /var/www/workbench/logs/cron.log 2>&1
```

---

## 常见问题

### 1. 静态文件404

```bash
# 确保收集了静态文件
python manage.py collectstatic --noinput

# 检查Nginx配置中的路径
sudo nginx -t
```

### 2. 数据库连接失败

```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 测试连接
psql -U workbench_user -d workbench -h localhost
```

### 3. 权限问题

```bash
# 修复文件权限
sudo chown -R workbench:workbench /var/www/workbench
sudo chmod -R 755 /var/www/workbench
sudo chmod 600 /var/www/workbench/.env
```

### 4. Gunicorn启动失败

```bash
# 查看日志
sudo journalctl -u workbench -f

# 手动测试
cd /var/www/workbench
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 workspace.wsgi:application
```

### 5. CSRF验证失败

确保 `CSRF_TRUSTED_ORIGINS` 包含正确的域名：

```python
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

---

## 快速部署命令汇总

```bash
# 一键部署脚本
#!/bin/bash

# 更新代码
cd /var/www/workbench
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 收集静态文件
python manage.py collectstatic --noinput

# 数据库迁移
python manage.py migrate

# 重启服务
sudo systemctl restart workbench
sudo systemctl restart nginx

echo "部署完成！"
```

---

## 备份策略

### 数据库备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/workbench"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL备份
pg_dump -U workbench_user workbench > $BACKUP_DIR/db_$DATE.sql

# SQLite备份（如果使用SQLite）
# cp /var/www/workbench/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# 保留最近7天的备份
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/db_$DATE.sql"
```

设置定时备份：

```bash
# 每天凌晨3点备份
0 3 * * * /var/www/workbench/backup.sh >> /var/www/workbench/logs/backup.log 2>&1
```

---

## 监控与日志

### 日志位置

- **Gunicorn访问日志**: `/var/www/workbench/logs/access.log`
- **Gunicorn错误日志**: `/var/www/workbench/logs/error.log`
- **Nginx访问日志**: `/var/log/nginx/access.log`
- **Nginx错误日志**: `/var/log/nginx/error.log`

### 查看实时日志

```bash
# 应用日志
tail -f /var/www/workbench/logs/error.log

# Nginx日志
tail -f /var/log/nginx/error.log

# 系统日志
sudo journalctl -u workbench -f
```

---

部署完成后，访问你的域名即可使用工作台应用！