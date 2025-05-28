from app import app, db, MonthlyProfit
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_monthly_profit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_monthly_profit_table():
    try:
        with app.app_context():
            # Check if the monthly_profit table exists in the database
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                logger.info("monthly_profit table already exists in the database")
            else:
                logger.info("monthly_profit table does not exist, creating it now...")
                
                # Create the monthly_profit table using SQLAlchemy
                db.create_all(tables=[MonthlyProfit.__table__])
                
                # Verify the table was created
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'")
                if cursor.fetchone() is not None:
                    logger.info("Successfully created monthly_profit table")
                else:
                    logger.error("Failed to create monthly_profit table")
            
            # Close the connection
            conn.close()
            
            # Recalculate monthly profits if needed
            from app import recalculate_monthly_profits
            recalculate_monthly_profits()
            logger.info("Monthly profits recalculated")
            
    except Exception as e:
        logger.error(f"Error fixing monthly_profit table: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Starting monthly_profit table fix...")
    fix_monthly_profit_table()
    print("Completed monthly_profit table fix. Check fix_monthly_profit.log for details.")
