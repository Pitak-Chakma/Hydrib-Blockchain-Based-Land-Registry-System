#!/usr/bin/env python3
"""
Health Check Script for Hydrib Land Registry System
Monitors application health and sends alerts if issues are detected
"""

import os
import sys
import time
import json
import sqlite3
import requests
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Configuration
APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'land_registry.db')
LOG_FILE = os.environ.get('HEALTH_CHECK_LOG', 'health_check.log')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'admin@landregistry.gov')
SMTP_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
SMTP_PORT = int(os.environ.get('MAIL_PORT', '587'))
SMTP_USERNAME = os.environ.get('MAIL_USERNAME', '')
SMTP_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '300'))  # 5 minutes
MAX_RESPONSE_TIME = int(os.environ.get('MAX_RESPONSE_TIME', '5'))  # seconds
DISK_THRESHOLD = float(os.environ.get('DISK_THRESHOLD', '90.0'))  # Percentage

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

class HealthChecker:
    def __init__(self):
        self.last_alert_time = {}
        self.alert_cooldown = timedelta(hours=1)  # Don't spam alerts
        
    def check_web_application(self):
        """Check if the web application is responding"""
        try:
            start_time = time.time()
            response = requests.get(f"{APP_URL}/", timeout=MAX_RESPONSE_TIME)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"Web application OK (response time: {response_time:.2f}s)")
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                logger.warning(f"Web application returned status {response.status_code}")
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Web application timeout (>{MAX_RESPONSE_TIME}s)")
            return {
                'status': 'unhealthy',
                'error': 'Timeout',
                'response_time': MAX_RESPONSE_TIME
            }
        except requests.exceptions.ConnectionError:
            logger.error("Web application connection failed")
            return {
                'status': 'unhealthy',
                'error': 'Connection failed'
            }
        except Exception as e:
            logger.error(f"Web application check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_database(self):
        """Check database connectivity and basic operations"""
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Test basic query
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            query_time = time.time() - start_time
            
            # Test write operation
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            conn.close()
            
            if integrity_result == 'ok':
                logger.info(f"Database OK (users: {user_count}, query time: {query_time:.3f}s)")
                return {
                    'status': 'healthy',
                    'user_count': user_count,
                    'query_time': query_time,
                    'integrity': integrity_result
                }
            else:
                logger.error(f"Database integrity check failed: {integrity_result}")
                return {
                    'status': 'unhealthy',
                    'error': f"Integrity check failed: {integrity_result}"
                }
                
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error: {e}")
            return {
                'status': 'unhealthy',
                'error': f"Database error: {e}"
            }
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            # Check application directory
            app_stat = os.statvfs('/opt/landregistry' if os.path.exists('/opt/landregistry') else '.')
            app_free_gb = (app_stat.f_bavail * app_stat.f_frsize) / (1024**3)
            
            # Check data directory
            data_path = '/var/lib/landregistry' if os.path.exists('/var/lib/landregistry') else '.'
            data_stat = os.statvfs(data_path)
            data_free_gb = (data_stat.f_bavail * data_stat.f_frsize) / (1024**3)
            
            # Check log directory
            log_path = '/var/log/landregistry' if os.path.exists('/var/log/landregistry') else '.'
            log_stat = os.statvfs(log_path)
            log_free_gb = (log_stat.f_bavail * log_stat.f_frsize) / (1024**3)
            
            min_free_gb = 1.0  # Alert if less than 1GB free
            
            if min(app_free_gb, data_free_gb, log_free_gb) > min_free_gb:
                logger.info(f"Disk space OK (app: {app_free_gb:.1f}GB, data: {data_free_gb:.1f}GB, log: {log_free_gb:.1f}GB)")
                return {
                    'status': 'healthy',
                    'app_free_gb': app_free_gb,
                    'data_free_gb': data_free_gb,
                    'log_free_gb': log_free_gb
                }
            else:
                logger.warning(f"Low disk space (app: {app_free_gb:.1f}GB, data: {data_free_gb:.1f}GB, log: {log_free_gb:.1f}GB)")
                return {
                    'status': 'warning',
                    'app_free_gb': app_free_gb,
                    'data_free_gb': data_free_gb,
                    'log_free_gb': log_free_gb,
                    'error': 'Low disk space'
                }
                
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_log_files(self):
        """Check for recent errors in log files"""
        try:
            log_files = [
                '/var/log/landregistry/app.log',
                '/var/log/landregistry/error.log',
                'app.log'  # Fallback for development
            ]
            
            error_count = 0
            recent_errors = []
            cutoff_time = datetime.now() - timedelta(minutes=30)
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()[-100:]  # Check last 100 lines
                            
                        for line in lines:
                            if 'ERROR' in line or 'CRITICAL' in line:
                                try:
                                    # Try to parse timestamp
                                    timestamp_str = line.split(' - ')[0]
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                    
                                    if timestamp > cutoff_time:
                                        error_count += 1
                                        recent_errors.append(line.strip())
                                except:
                                    # If timestamp parsing fails, count it anyway
                                    error_count += 1
                                    recent_errors.append(line.strip())
                                    
                    except Exception as e:
                        logger.warning(f"Could not read log file {log_file}: {e}")
            
            if error_count == 0:
                logger.info("No recent errors in log files")
                return {
                    'status': 'healthy',
                    'error_count': error_count
                }
            elif error_count < 5:
                logger.warning(f"Found {error_count} recent errors in logs")
                return {
                    'status': 'warning',
                    'error_count': error_count,
                    'recent_errors': recent_errors[:3]  # Show first 3 errors
                }
            else:
                logger.error(f"Found {error_count} recent errors in logs")
                return {
                    'status': 'unhealthy',
                    'error_count': error_count,
                    'recent_errors': recent_errors[:5]  # Show first 5 errors
                }
                
        except Exception as e:
            logger.error(f"Log file check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def send_alert(self, subject, message):
        """Send email alert"""
        if not ALERT_EMAIL or not SMTP_USERNAME:
            logger.warning("Email alerts not configured")
            return False
            
        # Check cooldown
        now = datetime.now()
        if subject in self.last_alert_time:
            if now - self.last_alert_time[subject] < self.alert_cooldown:
                logger.info(f"Alert cooldown active for: {subject}")
                return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f"[Hydrib Alert] {subject}"
            
            body = f"""
Hydrib Land Registry System Alert

Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Server: {os.uname().nodename if hasattr(os, 'uname') else 'Unknown'}

{message}

Please investigate immediately.

---
This is an automated alert from the Hydrib monitoring system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            self.last_alert_time[subject] = now
            logger.info(f"Alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def run_health_checks(self):
        """Run all health checks and return results"""
        logger.info("Starting health checks...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'web_application': self.check_web_application(),
                'database': self.check_database(),
                'disk_space': self.check_disk_space(),
                'log_files': self.check_log_files()
            }
        }
        
        # Determine overall status
        statuses = [check['status'] for check in results['checks'].values()]
        
        if 'unhealthy' in statuses:
            results['overall_status'] = 'unhealthy'
        elif 'warning' in statuses:
            results['overall_status'] = 'warning'
        else:
            results['overall_status'] = 'healthy'
        
        # Send alerts for unhealthy components
        for check_name, check_result in results['checks'].items():
            if check_result['status'] == 'unhealthy':
                error_msg = check_result.get('error', 'Unknown error')
                self.send_alert(
                    f"{check_name.replace('_', ' ').title()} Failure",
                    f"Health check failed for {check_name}:\n\nError: {error_msg}\n\nFull result: {json.dumps(check_result, indent=2)}"
                )
        
        logger.info(f"Health checks completed. Overall status: {results['overall_status']}")
        return results
    
    def save_results(self, results):
        """Save health check results to file"""
        try:
            results_file = '/var/log/landregistry/health_results.json'
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save health check results: {e}")

def main():
    """Main function for health monitoring"""
    checker = HealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # Run as daemon
        logger.info(f"Starting health check daemon (interval: {CHECK_INTERVAL}s)")
        
        while True:
            try:
                results = checker.run_health_checks()
                checker.save_results(results)
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Health check daemon stopped")
                break
            except Exception as e:
                logger.error(f"Health check daemon error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        # Run once
        results = checker.run_health_checks()
        checker.save_results(results)
        
        # Print results
        print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        if results['overall_status'] == 'unhealthy':
            sys.exit(1)
        elif results['overall_status'] == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)

if __name__ == '__main__':
    main()