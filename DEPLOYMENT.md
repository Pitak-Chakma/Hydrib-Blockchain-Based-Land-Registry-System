# Hydrib Land Registry System - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Hydrib Land Registry System in a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Configuration](#configuration)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04 LTS or newer (recommended)
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended
- **Network**: Static IP address, ports 80 and 443 accessible

### Software Dependencies

- Python 3.8+
- Nginx
- SQLite3
- SSL certificate (Let's Encrypt recommended)
- Email server (for notifications)

## Quick Deployment

For a quick automated deployment, use the provided deployment script:

```bash
# Clone the repository
git clone <repository-url>
cd Hydrib-Blockchain-Based-Land-Registry-System

# Make deployment script executable
chmod +x deploy.sh

# Run deployment (as root)
sudo ./deploy.sh
```

The script will:
- Install all dependencies
- Create necessary users and directories
- Configure the application
- Set up systemd service
- Configure nginx
- Set up automated backups
- Start all services

## Manual Deployment

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 curl supervisor certbot python3-certbot-nginx

# Create application user
sudo groupadd -r landregistry
sudo useradd -r -g landregistry -d /opt/landregistry -s /bin/bash landregistry
```

### Step 2: Application Setup

```bash
# Create directories
sudo mkdir -p /opt/landregistry
sudo mkdir -p /var/lib/landregistry/{uploads,backups}
sudo mkdir -p /var/log/landregistry

# Clone application
sudo git clone <repository-url> /opt/landregistry
sudo chown -R landregistry:landregistry /opt/landregistry

# Create virtual environment
sudo -u landregistry python3 -m venv /opt/landregistry/venv
sudo -u landregistry /opt/landregistry/venv/bin/pip install -r /opt/landregistry/requirements.txt
```

### Step 3: Configuration

```bash
# Copy environment configuration
sudo cp /opt/landregistry/.env.production /opt/landregistry/.env

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sudo sed -i "s/CHANGE-THIS-TO-A-SECURE-RANDOM-STRING-IN-PRODUCTION/$SECRET_KEY/g" /opt/landregistry/.env

# Set proper permissions
sudo chown landregistry:landregistry /opt/landregistry/.env
sudo chmod 600 /opt/landregistry/.env
```

### Step 4: Database Initialization

```bash
# Initialize database
sudo -u landregistry /opt/landregistry/venv/bin/python /opt/landregistry/app.py
```

### Step 5: Service Configuration

```bash
# Install systemd service
sudo cp /opt/landregistry/landregistry.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable landregistry
sudo systemctl start landregistry
```

### Step 6: Nginx Configuration

```bash
# Configure nginx
sudo cp /opt/landregistry/nginx.conf /etc/nginx/sites-available/landregistry
sudo ln -s /etc/nginx/sites-available/landregistry /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: SSL Certificate

```bash
# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## Docker Deployment

### Using Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd Hydrib-Blockchain-Based-Land-Registry-System

# Create environment file
cp .env.production .env
# Edit .env with your configuration

# Generate SSL certificates (place in ./ssl/ directory)
# Or use Let's Encrypt with certbot

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f web
```

### Building Custom Image

```bash
# Build image
docker build -t hydrib-landregistry .

# Run container
docker run -d \
  --name landregistry \
  -p 8000:8000 \
  -v /var/lib/landregistry:/var/lib/landregistry \
  -v /var/log/landregistry:/var/log/landregistry \
  --env-file .env \
  hydrib-landregistry
```

## Configuration

### Environment Variables

Key environment variables that must be configured:

```bash
# Security (REQUIRED)
SECRET_KEY=your-secure-secret-key

# Database
DATABASE_PATH=/var/lib/landregistry/land_registry.db

# File uploads
UPLOAD_FOLDER=/var/lib/landregistry/uploads

# Email notifications
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ALERT_EMAIL=admin@yourdomain.com

# Admin settings
ADMIN_EMAIL=admin@yourdomain.com
```

### Application Configuration

Edit `/opt/landregistry/.env` to customize:

- Session timeout
- Rate limiting
- File upload limits
- Backup settings
- Logging levels

## Security

### SSL/TLS Configuration

1. **Obtain SSL Certificate**:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Configure Strong Ciphers**: The nginx configuration includes secure cipher suites

3. **Enable HSTS**: Strict Transport Security is enabled by default

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Security Headers

The application automatically adds security headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy
- Strict-Transport-Security

### Regular Security Updates

```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring

### Health Checks

The application includes built-in health monitoring:

```bash
# Manual health check
curl http://localhost:8000/health

# Run comprehensive health check
python3 /opt/landregistry/health_check.py

# Start health monitoring daemon
python3 /opt/landregistry/health_check.py --daemon
```

### Log Monitoring

Logs are stored in `/var/log/landregistry/`:

- `app.log` - Application logs
- `access.log` - Nginx access logs
- `error.log` - Nginx error logs
- `backup.log` - Backup operation logs
- `health_check.log` - Health monitoring logs

### System Monitoring

```bash
# Check service status
sudo systemctl status landregistry
sudo systemctl status nginx

# View real-time logs
sudo journalctl -u landregistry -f
sudo tail -f /var/log/landregistry/app.log

# Check resource usage
htop
df -h
```

## Backup and Recovery

### Automated Backups

Backups are automatically configured via cron:

```bash
# View backup cron job
sudo crontab -u landregistry -l

# Manual backup
sudo -u landregistry /opt/landregistry/venv/bin/python /opt/landregistry/backup_script.py

# List backups
ls -la /var/backups/landregistry/
```

### Backup Components

1. **Database**: SQLite database with all land records
2. **Uploaded Files**: Property documents and images
3. **Configuration**: Environment and configuration files

### Recovery Procedure

```bash
# Stop application
sudo systemctl stop landregistry

# Restore database
gunzip -c /var/backups/landregistry/database_backup_YYYYMMDD_HHMMSS.db.gz > /var/lib/landregistry/land_registry.db

# Restore uploads
tar -xzf /var/backups/landregistry/uploads_backup_YYYYMMDD_HHMMSS.tar.gz -C /var/lib/landregistry/

# Set permissions
sudo chown -R landregistry:landregistry /var/lib/landregistry

# Start application
sudo systemctl start landregistry
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   ```bash
   sudo systemctl status landregistry
   sudo journalctl -u landregistry -n 50
   ```

2. **Database Connection Errors**:
   ```bash
   # Check database file permissions
   ls -la /var/lib/landregistry/land_registry.db
   
   # Test database connectivity
   sqlite3 /var/lib/landregistry/land_registry.db "SELECT COUNT(*) FROM users;"
   ```

3. **Nginx Configuration Issues**:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

4. **SSL Certificate Problems**:
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

### Performance Issues

1. **Slow Database Queries**:
   ```bash
   # Run performance analysis
   python3 /opt/landregistry/performance_monitor.py
   ```

2. **High Memory Usage**:
   ```bash
   # Check memory usage
   free -h
   ps aux | grep gunicorn
   ```

3. **Disk Space Issues**:
   ```bash
   # Check disk usage
   df -h
   du -sh /var/lib/landregistry/*
   ```

## Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Review application logs
   - Check backup integrity
   - Monitor disk space
   - Review security logs

2. **Monthly**:
   - Update system packages
   - Rotate log files
   - Review performance metrics
   - Test backup restoration

3. **Quarterly**:
   - Security audit
   - Performance optimization
   - Capacity planning
   - Disaster recovery testing

### Update Procedure

```bash
# Backup current installation
sudo -u landregistry /opt/landregistry/venv/bin/python /opt/landregistry/backup_script.py

# Stop application
sudo systemctl stop landregistry

# Update code
cd /opt/landregistry
sudo -u landregistry git pull origin main

# Update dependencies
sudo -u landregistry /opt/landregistry/venv/bin/pip install -r requirements.txt

# Run database migrations (if any)
# sudo -u landregistry /opt/landregistry/venv/bin/python migrate.py

# Start application
sudo systemctl start landregistry

# Verify deployment
curl http://localhost:8000/health
```

### Log Rotation

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/landregistry << EOF
/var/log/landregistry/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 landregistry landregistry
    postrotate
        systemctl reload landregistry
    endscript
}
EOF
```

## Support

For additional support:

1. Check the application logs: `/var/log/landregistry/app.log`
2. Review the health check results: `/var/log/landregistry/health_results.json`
3. Run the performance monitor: `python3 /opt/landregistry/performance_monitor.py`
4. Contact the development team with detailed error information

---

**Note**: Always test deployments in a staging environment before applying to production.