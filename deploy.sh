#!/bin/bash

# Hydrib Land Registry System - Production Deployment Script
# This script automates the deployment process for production environments

set -e  # Exit on any error

# Configuration
APP_NAME="landregistry"
APP_USER="landregistry"
APP_GROUP="landregistry"
APP_DIR="/opt/landregistry"
DATA_DIR="/var/lib/landregistry"
LOG_DIR="/var/log/landregistry"
BACKUP_DIR="/var/backups/landregistry"
SERVICE_FILE="landregistry.service"
NGINX_AVAILABLE="/etc/nginx/sites-available/landregistry"
NGINX_ENABLED="/etc/nginx/sites-enabled/landregistry"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        sqlite3 \
        curl \
        supervisor \
        certbot \
        python3-certbot-nginx
    
    log_success "System dependencies installed"
}

# Create application user
create_user() {
    log "Creating application user..."
    
    if ! id "$APP_USER" &>/dev/null; then
        groupadd -r "$APP_GROUP"
        useradd -r -g "$APP_GROUP" -d "$APP_DIR" -s /bin/bash "$APP_USER"
        log_success "User $APP_USER created"
    else
        log_warning "User $APP_USER already exists"
    fi
}

# Create directories
create_directories() {
    log "Creating application directories..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$DATA_DIR/uploads"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Set ownership
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    chown -R "$APP_USER:$APP_GROUP" "$DATA_DIR"
    chown -R "$APP_USER:$APP_GROUP" "$LOG_DIR"
    chown -R "$APP_USER:$APP_GROUP" "$BACKUP_DIR"
    
    # Set permissions
    chmod 755 "$APP_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$BACKUP_DIR"
    
    log_success "Directories created and configured"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    # Copy application files
    cp -r . "$APP_DIR/"
    
    # Create virtual environment
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
    
    # Install Python dependencies
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
    
    # Set permissions
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    
    log_success "Application deployed"
}

# Configure environment
configure_environment() {
    log "Configuring environment..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$APP_DIR/.env" ]]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        
        # Generate secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/your-super-secret-key-here-change-this-in-production/$SECRET_KEY/g" "$APP_DIR/.env"
        
        # Update paths for production
        sed -i "s|^FLASK_ENV=development|FLASK_ENV=production|g" "$APP_DIR/.env"
        sed -i "s|^FLASK_DEBUG=True|FLASK_DEBUG=False|g" "$APP_DIR/.env"
        sed -i "s|^DATABASE_PATH=land_registry.db|DATABASE_PATH=$DATA_DIR/land_registry.db|g" "$APP_DIR/.env"
        sed -i "s|^UPLOAD_FOLDER=uploads|UPLOAD_FOLDER=$DATA_DIR/uploads|g" "$APP_DIR/.env"
        sed -i "s|^LOG_FILE=app.log|LOG_FILE=$LOG_DIR/app.log|g" "$APP_DIR/.env"
        
        chown "$APP_USER:$APP_GROUP" "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"
        
        log_success "Environment configured"
    else
        log_warning "Environment file already exists"
    fi
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    cd "$APP_DIR"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" -c "
from app import create_app
from config import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    from app import init_db
    init_db()
print('Database initialized successfully')
"
    
    log_success "Database initialized"
}

# Configure systemd service
configure_systemd() {
    log "Configuring systemd service..."
    
    cp "$SERVICE_FILE" "/etc/systemd/system/"
    systemctl daemon-reload
    systemctl enable "$APP_NAME"
    
    log_success "Systemd service configured"
}

# Configure nginx
configure_nginx() {
    log "Configuring nginx..."
    
    # Create nginx site configuration
    cat > "$NGINX_AVAILABLE" << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $DATA_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 16M;
}
EOF
    
    # Enable site
    ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    log_success "Nginx configured"
}

# Configure backup cron job
configure_backup() {
    log "Configuring backup cron job..."
    
    # Create backup script
    chmod +x "$APP_DIR/backup_script.py"
    
    # Add cron job for daily backups at 2 AM
    (crontab -u "$APP_USER" -l 2>/dev/null; echo "0 2 * * * $APP_DIR/venv/bin/python $APP_DIR/backup_script.py") | crontab -u "$APP_USER" -
    
    log_success "Backup cron job configured"
}

# Start services
start_services() {
    log "Starting services..."
    
    systemctl start "$APP_NAME"
    systemctl restart nginx
    
    # Check service status
    if systemctl is-active --quiet "$APP_NAME"; then
        log_success "$APP_NAME service started successfully"
    else
        log_error "Failed to start $APP_NAME service"
        systemctl status "$APP_NAME"
        exit 1
    fi
    
    if systemctl is-active --quiet nginx; then
        log_success "Nginx started successfully"
    else
        log_error "Failed to start nginx"
        systemctl status nginx
        exit 1
    fi
}

# Setup SSL certificate
setup_ssl() {
    read -p "Do you want to setup SSL certificate with Let's Encrypt? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your domain name: " DOMAIN_NAME
        read -p "Enter your email address: " EMAIL_ADDRESS
        
        log "Setting up SSL certificate for $DOMAIN_NAME..."
        
        certbot --nginx -d "$DOMAIN_NAME" --email "$EMAIL_ADDRESS" --agree-tos --non-interactive
        
        log_success "SSL certificate configured"
    fi
}

# Display deployment summary
show_summary() {
    log_success "Deployment completed successfully!"
    echo
    echo "=== Deployment Summary ==="
    echo "Application Directory: $APP_DIR"
    echo "Data Directory: $DATA_DIR"
    echo "Log Directory: $LOG_DIR"
    echo "Backup Directory: $BACKUP_DIR"
    echo "Service Name: $APP_NAME"
    echo
    echo "=== Useful Commands ==="
    echo "Check service status: systemctl status $APP_NAME"
    echo "View logs: journalctl -u $APP_NAME -f"
    echo "Restart service: systemctl restart $APP_NAME"
    echo "Check nginx status: systemctl status nginx"
    echo "View application logs: tail -f $LOG_DIR/app.log"
    echo
    echo "=== Next Steps ==="
    echo "1. Update DNS records to point to this server"
    echo "2. Configure firewall rules (ports 80, 443)"
    echo "3. Set up monitoring and alerting"
    echo "4. Review and update environment variables in $APP_DIR/.env"
    echo "5. Test the application thoroughly"
}

# Main deployment function
main() {
    log "Starting Hydrib Land Registry System deployment..."
    
    check_root
    install_dependencies
    create_user
    create_directories
    deploy_application
    configure_environment
    initialize_database
    configure_systemd
    configure_nginx
    configure_backup
    start_services
    setup_ssl
    show_summary
}

# Run main function
main "$@"