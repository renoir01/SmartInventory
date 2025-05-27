from app import app, db, Sale, Product, User
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

with app.app_context():
    # Check total sales
    total_sales = Sale.query.count()
    print(f"Total sales in database: {total_sales}")
    
    # Get all sales with their dates
    print("\nAll sales with dates:")
    all_sales = Sale.query.order_by(Sale.date_sold.desc()).all()
    for sale in all_sales:
        print(f"ID: {sale.id}, Date: {sale.date_sold}, Product: {sale.product.name}, Amount: {sale.total_price}")
    
    # Check today's date range
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    print(f"\nToday's date range: {today_start} to {today_end}")
    
    # Check sales for today using different methods
    print("\nSales for today using between:")
    today_sales_between = Sale.query.filter(Sale.date_sold.between(today_start, today_end)).all()
    print(f"Count: {len(today_sales_between)}")
    for sale in today_sales_between:
        print(f"ID: {sale.id}, Date: {sale.date_sold}")
    
    print("\nSales for today using >= and <=:")
    today_sales_explicit = Sale.query.filter(
        Sale.date_sold >= today_start,
        Sale.date_sold <= today_end
    ).all()
    print(f"Count: {len(today_sales_explicit)}")
    for sale in today_sales_explicit:
        print(f"ID: {sale.id}, Date: {sale.date_sold}")
    
    # Try with date string comparison
    today_str = today.strftime('%Y-%m-%d')
    print(f"\nSales for today using date string comparison (date: {today_str}):")
    today_sales_str = Sale.query.filter(db.func.date(Sale.date_sold) == today_str).all()
    print(f"Count: {len(today_sales_str)}")
    for sale in today_sales_str:
        print(f"ID: {sale.id}, Date: {sale.date_sold}")
    
    # Check sales for the last 7 days
    week_ago = today - timedelta(days=7)
    print(f"\nSales for the last 7 days (since {week_ago}):")
    week_sales = Sale.query.filter(Sale.date_sold >= datetime.combine(week_ago, datetime.min.time())).all()
    print(f"Count: {len(week_sales)}")
    for sale in week_sales:
        print(f"ID: {sale.id}, Date: {sale.date_sold}")
