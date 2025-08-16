#!/usr/bin/env python3
"""
Backup Script for Hydrib Land Registry System
Performs automated backups of database and uploaded files
"""

import os
import sqlite3
import shutil
import tarfile
import gzip
import datetime
import logging
import json
from pathlib import Path

# Configuration
BACKUP_DIR = os.environ.get('BACKUP_PATH', '/var/backups/landregistry')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'land_registry.db')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
LOG_FILE = os.environ.get('BACKUP_LOG_FILE', '/var/log/landregistry/backup.log')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_backup_directory():
    """Create backup directory if it doesn't exist"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Backup directory: {BACKUP_DIR}")

def backup_database():
    """Create a backup of the SQLite database"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"database_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # Create database backup using SQLite backup API
        source_conn = sqlite3.connect(DATABASE_PATH)
        backup_conn = sqlite3.connect(backup_path)
        
        source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        # Compress the backup
        compressed_path = f"{backup_path}.gz"
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed backup
        os.remove(backup_path)
        
        logger.info(f"Database backup created: {compressed_path}")
        return compressed_path
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return None

def backup_uploads():
    """Create a backup of uploaded files"""
    if not os.path.exists(UPLOAD_FOLDER):
        logger.warning(f"Upload folder not found: {UPLOAD_FOLDER}")
        return None
        
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"uploads_backup_{timestamp}.tar.gz"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(UPLOAD_FOLDER, arcname='uploads')
        
        logger.info(f"Uploads backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Uploads backup failed: {e}")
        return None

def create_backup_manifest(db_backup, uploads_backup):
    """Create a manifest file with backup information"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    manifest_filename = f"backup_manifest_{timestamp}.json"
    manifest_path = os.path.join(BACKUP_DIR, manifest_filename)
    
    manifest = {
        'timestamp': datetime.datetime.now().isoformat(),
        'database_backup': os.path.basename(db_backup) if db_backup else None,
        'uploads_backup': os.path.basename(uploads_backup) if uploads_backup else None,
        'database_size': os.path.getsize(db_backup) if db_backup else 0,
        'uploads_size': os.path.getsize(uploads_backup) if uploads_backup else 0,
        'retention_days': RETENTION_DAYS
    }
    
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Backup manifest created: {manifest_path}")
        return manifest_path
        
    except Exception as e:
        logger.error(f"Manifest creation failed: {e}")
        return None

def cleanup_old_backups():
    """Remove backups older than retention period"""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=RETENTION_DAYS)
    removed_count = 0
    
    try:
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            
            if os.path.isfile(file_path):
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {filename}")
        
        logger.info(f"Cleanup completed. Removed {removed_count} old backup files")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

def verify_backup_integrity(backup_path):
    """Verify backup file integrity"""
    if not backup_path or not os.path.exists(backup_path):
        return False
        
    try:
        if backup_path.endswith('.gz'):
            with gzip.open(backup_path, 'rb') as f:
                f.read(1024)  # Try to read some data
        elif backup_path.endswith('.tar.gz'):
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.getmembers()  # Try to list contents
        
        logger.info(f"Backup integrity verified: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Backup integrity check failed for {backup_path}: {e}")
        return False

def get_backup_statistics():
    """Get backup directory statistics"""
    try:
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        logger.info(f"Backup statistics: {file_count} files, {total_size / (1024*1024):.2f} MB total")
        
    except Exception as e:
        logger.error(f"Failed to get backup statistics: {e}")

def main():
    """Main backup function"""
    logger.info("Starting backup process")
    
    # Create backup directory
    create_backup_directory()
    
    # Perform backups
    db_backup = backup_database()
    uploads_backup = backup_uploads()
    
    # Verify backups
    db_valid = verify_backup_integrity(db_backup)
    uploads_valid = verify_backup_integrity(uploads_backup)
    
    if not db_valid:
        logger.error("Database backup verification failed")
    if uploads_backup and not uploads_valid:
        logger.error("Uploads backup verification failed")
    
    # Create manifest
    if db_backup or uploads_backup:
        create_backup_manifest(db_backup, uploads_backup)
    
    # Cleanup old backups
    cleanup_old_backups()
    
    # Show statistics
    get_backup_statistics()
    
    logger.info("Backup process completed")

if __name__ == '__main__':
    main()