#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from config import get_config

# Get configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
config_class = get_config(config_name)

# Validate production configuration
if config_name == 'production':
    try:
        config_class.validate_production_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

# Create application
application = create_app(config_class)

if __name__ == "__main__":
    application.run()