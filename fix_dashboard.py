#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fix Dashboard Script
This script creates the monthly_profit table if it doesn't exist
and adds a sample record to prevent errors in the admin dashboard.
"""

from app import app, db, MonthlyProfit
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def create_monthly_profit_table():
    """Create the monthly_profit table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if table exists
            result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'"))
            if not result.scalar():
                logger.info("Creating monthly_profit table...")
                db.create_all()
                logger.info("Table created successfully.")
            else:
                logger.info("monthly_profit table already exists.")
                
            # Check if there are any records
            count = db.session.execute(db.text("SELECT COUNT(*) FROM monthly_profit")).scalar()
            if count == 0:
                # Add a sample record for the current month
                today = datetime.now()
                current_year = today.year
                current_month = today.month
                
                # Create a sample monthly profit record
                sample_profit = MonthlyProfit(
                    year=current_year,
                    month=current_month,
                    total_revenue=0,
                    total_cost=0,
                    total_profit=0,
                    sale_count=0
                )
                
                db.session.add(sample_profit)
                db.session.commit()
                logger.info(f"Added sample record for {current_month}/{current_year}")
            else:
                logger.info(f"monthly_profit table has {count} records.")
                
            logger.info("Database setup completed successfully.")
            
        except Exception as e:
            logger.error(f"Error setting up database: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_monthly_profit_table()
