from app import app, db, MonthlyProfit
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("recreate_monthly_profit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def recreate_monthly_profit_table():
    try:
        with app.app_context():
            # Check if the monthly_profit table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'monthly_profit' in tables:
                logger.info("monthly_profit table already exists")
            else:
                logger.info("Creating monthly_profit table...")
                # Create only the monthly_profit table
                db.create_all(tables=[MonthlyProfit.__table__])
                logger.info("monthly_profit table created successfully")
                
            # Verify the table was created
            tables_after = inspector.get_table_names()
            if 'monthly_profit' in tables_after:
                logger.info("Verification: monthly_profit table exists in the database")
            else:
                logger.error("Verification failed: monthly_profit table was not created")
                
    except Exception as e:
        logger.error(f"Error recreating monthly_profit table: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_monthly_profit_table()
