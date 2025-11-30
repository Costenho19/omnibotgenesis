#!/usr/bin/env python3
"""
OMNIX Dashboard Launcher for Railway
Starts the Performance Dashboard V6.4 INSTITUTIONAL+ 
on the port specified by Railway (default 8000)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    os.environ.setdefault('PORT', '8000')
    
    from omnix_dashboard.app import app, logger
    
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 OMNIX Dashboard V6.4 INSTITUTIONAL+ starting on port {port}")
    logger.info("📊 Real data mode - Connected to PostgreSQL")
    
    app.run(host='0.0.0.0', port=port, debug=False)
