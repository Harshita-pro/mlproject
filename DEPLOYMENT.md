# 🚀 Production Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests pass
- [ ] No debug mode enabled
- [ ] Environment variables configured
- [ ] HTTPS enabled
- [ ] Logging configured
- [ ] Error tracking setup
- [ ] Database backups configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers set

## Deployment Options

### 1. Local Server (Development)

```bash
# Activate environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Run development server
python app.py
```

**URL**: http://localhost:5000

**Pros**: Easy setup, good for testing
**Cons**: Not suitable for production, no scalability

---

### 2. Gunicorn (Production - Recommended for small/medium deployments)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Run with more workers for higher load
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 120 app:app
```

**Pros**: Production-ready, good performance, simple setup
**Cons**: Requires manual server management

---

### 3. Docker (Containerized Deployment)

#### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Create .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv
.git
.gitignore
.env
.DS_Store
static/uploads/*
```

#### Build and Run

```bash
# Build image
docker build -t medicine-identifier:latest .

# Run container
docker run -p 5000:5000 -e FLASK_ENV=production medicine-identifier:latest

# Push to Docker Hub
docker tag medicine-identifier:latest your-username/medicine-identifier:latest
docker push your-username/medicine-identifier:latest
```

---

### 4. Heroku (Cloud Deployment - Free tier available)

#### Create Procfile

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

#### Create runtime.txt

```
python-3.9.16
```

#### Deploy

```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

**URL**: https://your-app-name.herokuapp.com

---

### 5. AWS EC2 (Full Control)

#### Setup

```bash
# Connect to EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system
sudo yum update -y
sudo yum install python3 python3-pip git -y

# Clone repository
git clone your-repo-url
cd mlproject

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/medicine-identifier.service
```

#### Service File Content

```ini
[Unit]
Description=Medicine Identifier Flask App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/mlproject
Environment="PATH=/home/ec2-user/mlproject/venv/bin"
ExecStart=/home/ec2-user/mlproject/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

#### Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start medicine-identifier

# Enable on boot
sudo systemctl enable medicine-identifier

# Check status
sudo systemctl status medicine-identifier
```

---

### 6. Google Cloud Run (Serverless)

#### Setup

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build and deploy
gcloud run deploy medicine-identifier \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

### 7. Railway.app (Simple Cloud Deployment)

1. Push code to GitHub
2. Connect GitHub repo to Railway
3. Set environment variables
4. Deploy automatically

**URL**: `your-app-name.railway.app`

---

## Production Configuration

### Environment Variables

Create `.env` file:

```env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-here
MAX_FILE_SIZE=10485760
LOG_LEVEL=INFO
```

### Load Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()

app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
```

---

## Security Hardening

### 1. HTTPS Setup (Let's Encrypt + Nginx)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### 2. Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Firewall Configuration

```bash
# UFW on Ubuntu
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Monitoring & Logging

### 1. Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### 2. Error Tracking (Sentry)

```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 3. Performance Monitoring

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')
```

---

## Database Backup

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +"%Y%m%d_%H%M%S")

# Backup FAISS index
cp utils/medicine_index.faiss $BACKUP_DIR/medicine_index_$DATE.faiss

# Backup medicine data
cp utils/medicine_data.pkl $BACKUP_DIR/medicine_data_$DATE.pkl

# Keep last 30 days only
find $BACKUP_DIR -name "*.faiss" -mtime +30 -delete
find $BACKUP_DIR -name "*.pkl" -mtime +30 -delete

echo "Backup completed at $DATE"
```

Schedule with cron:

```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## Performance Optimization

### 1. Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/medicine/<name>')
@cache.cached(timeout=3600)
def get_medicine(name):
    ...
```

### 2. Database Indexing

```python
# Add index to frequently searched fields
df.index = df['Medicine Name']
df.index.name = 'medicine_index'
```

### 3. Load Balancing

Use HAProxy or Nginx to distribute traffic:

```nginx
upstream app_servers {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 5000;
    location / {
        proxy_pass http://app_servers;
    }
}
```

---

## Scaling Strategies

1. **Vertical**: Increase server resources (CPU, RAM)
2. **Horizontal**: Add more servers with load balancing
3. **Caching**: Redis/Memcached for frequently accessed data
4. **Database**: Move to managed service (Amazon RDS)
5. **CDN**: CloudFront or Cloudflare for static assets

---

## Rollback & Recovery

```bash
# Keep previous versions
docker tag medicine-identifier:latest medicine-identifier:v1.0
docker push your-repo/medicine-identifier:v1.0

# Rollback to previous version
docker run -p 5000:5000 your-repo/medicine-identifier:v1.0

# Database recovery
# Restore from latest backup
cp /backups/medicine_data_latest.pkl utils/medicine_data.pkl
```

---

## Monitoring Checklist

- [ ] Check application logs daily
- [ ] Monitor server CPU/Memory usage
- [ ] Track API response times
- [ ] Monitor error rates
- [ ] Review backup status
- [ ] Check SSL certificate expiry
- [ ] Verify uptime
- [ ] Monitor user feedback

---

## Support & Troubleshooting

**503 Service Unavailable**: Check if gunicorn process is running
**Connection Timeout**: Check firewall rules and SSL certificate
**High CPU Usage**: Check for slow queries or optimize OCR
**Memory Leaks**: Monitor with `top`, consider upgrading server

---

**Your app is now production-ready! 🚀**
