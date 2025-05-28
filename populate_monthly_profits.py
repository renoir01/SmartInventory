from app import app, db, recalculate_monthly_profits, MonthlyProfit
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("populate_monthly_profits.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def populate_monthly_profits():
    try:
        print("Starting monthly profit population...")
        
        # Connect to the database to check current state
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Check current monthly_profit records
        cursor.execute("SELECT COUNT(*) FROM monthly_profit")
        initial_count = cursor.fetchone()[0]
        print(f"Initial monthly_profit records: {initial_count}")
        
        # Close the connection
        conn.close()
        
        # Use the app context to recalculate profits
        with app.app_context():
            print("Recalculating monthly profits from sales data...")
            recalculate_monthly_profits()
            
            # Check if records were created
            profits = MonthlyProfit.query.all()
            print(f"After recalculation: {len(profits)} monthly profit records")
            
            # Print details of the records
            for profit in profits:
                print(f"Year: {profit.year}, Month: {profit.month}, Revenue: {profit.total_revenue}, Profit: {profit.total_profit}")
        
        print("Monthly profit population completed successfully")
        
    except Exception as e:
        print(f"Error populating monthly profits: {str(e)}")
        logger.error(f"Error populating monthly profits: {str(e)}")

if __name__ == "__main__":
    populate_monthly_profits()
