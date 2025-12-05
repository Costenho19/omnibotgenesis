"""
OMNIX Dashboard - Development Runner
Entry point for running the dashboard in development mode
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_dashboard.app import app
from omnix_dashboard.utils.database import get_database_url, init_database

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"OMNIX Dashboard V6.5.3 INSTITUTIONAL+ starting on port {port}")
    
    database_url = get_database_url()
    if database_url:
        logger.info("DATABASE_URL detected - attempting connection...")
        from omnix_dashboard.utils.database import DB_ERROR_MESSAGE
        if init_database():
            logger.info("Database connected successfully - REAL DATA MODE")
        else:
            logger.error(f"Database connection FAILED: {DB_ERROR_MESSAGE}")
    else:
        logger.warning("No DATABASE_URL found - Dashboard will show empty state")
    
    logger.info(f"Debug endpoint: http://localhost:{port}/api/debug")
    app.run(host='0.0.0.0', port=port, debug=False)
