from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set a strong, consistent SECRET_KEY for session management
# Using a fixed key for development, but in production this should be an environment variable
app.config['SECRET_KEY'] = 'SmartInventory_secure_key_2025_05_28'
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in files
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)
app.config['SESSION_USE_SIGNER'] = True  # Add a cryptographic signature to cookies

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Internationalization configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'locale'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Helper function for translations
def _(text, **variables):
    return text % variables if variables else text

# Try to initialize Babel with error handling
try:
    from flask_babel import Babel
    
    @app.route('/set_language/<language>')
    def set_language(language):
        session['language'] = language
        return redirect(request.referrer or url_for('index'))
    
    def get_locale():
        return session.get('language', 'en')
    
    # Initialize Babel with the locale selector
    babel = Babel(app, locale_selector=get_locale)
    
    # Import gettext after Babel is initialized
    from flask_babel import gettext as flask_gettext
    _ = flask_gettext
    
    @app.before_request
    def before_request():
        g._ = _
    
    has_babel = True
    logger.info("Flask-Babel initialized successfully")
    
except Exception as e:
    logger.warning(f"Flask-Babel initialization failed: {str(e)}")
    has_babel = False
    # Use the fallback translation function defined above

# Helper function to get current time in CAT timezone
def get_cat_time():
    cat_timezone = pytz.timezone('Africa/Kigali')  # Kigali is in Rwanda and uses CAT
    return datetime.now(cat_timezone)

# Database models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'cashier'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), default='Uncategorized')
    purchase_price = db.Column(db.Float, default=0)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields for package handling
    is_packaged = db.Column(db.Boolean, default=False)
    units_per_package = db.Column(db.Integer, default=1)
    individual_price = db.Column(db.Float, default=0)
    individual_stock = db.Column(db.Integer, default=0)
    
    def is_low_stock(self):
        if self.is_packaged:
            # Consider both package stock and individual units
            total_units = (self.stock * self.units_per_package) + self.individual_stock
            return total_units <= self.low_stock_threshold
        return self.stock <= self.low_stock_threshold
    
    def get_profit_margin(self):
        if self.purchase_price > 0:
            return ((self.price - self.purchase_price) / self.price) * 100
        return 100  # If purchase price is 0, profit margin is 100%
    
    def get_total_units(self):
        """Get the total number of units (both packaged and individual)"""
        if self.is_packaged:
            return (self.stock * self.units_per_package) + self.individual_stock
        return self.stock

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('sales', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cashier = db.relationship('User', backref=db.backref('sales', lazy=True))
    date_sold = db.Column(db.DateTime, default=get_cat_time)

class MonthlyProfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12 for Jan-Dec
    total_revenue = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    sale_count = db.Column(db.Integer, default=0)
    
    # Ensure year and month combination is unique
    __table_args__ = (db.UniqueConstraint('year', 'month', name='unique_year_month'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    """Home page route that shows the login page directly."""
    # Always render login page directly to avoid redirect loops
    return render_template('login.html')

# Emergency direct login routes for testing
@app.route('/direct-admin-login')
def direct_admin_login():
    """Emergency route to directly log in as admin for testing."""
    try:
        # Find the admin user
        admin = User.query.filter_by(role='admin').first()
        if admin:
            # Log in as admin
            login_user(admin)
            flash('Logged in as admin for testing', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin user not found', 'danger')
    except Exception as e:
        logger.error(f"Error in direct admin login: {str(e)}")
        flash('Error logging in', 'danger')
    return render_template('login.html')

@app.route('/direct-cashier-login')
def direct_cashier_login():
    """Emergency route to directly log in as cashier for testing."""
    try:
        # Find the cashier user
        cashier = User.query.filter_by(role='cashier').first()
        if cashier:
            # Log in as cashier
            login_user(cashier)
            flash('Logged in as cashier for testing', 'success')
            return redirect(url_for('cashier_dashboard'))
        else:
            flash('Cashier user not found', 'danger')
    except Exception as e:
        logger.error(f"Error in direct cashier login: {str(e)}")
        flash('Error logging in', 'danger')
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simplified login route to avoid redirect loops."""
    # For GET requests, just show the login page
    if request.method == 'GET':
        # If user is already logged in, redirect to appropriate dashboard
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'cashier':
                return redirect(url_for('cashier_dashboard'))
        return render_template('login.html')
    
    # For POST requests, handle login
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    if not username or not password:
        flash(_('Please enter both username and password'), 'danger')
        return render_template('login.html')
    
    # Special case for the 'epi' user with password 'Epi@654'
    if username == 'epi' and password == 'Epi@654':
        try:
            # Find the user
            user = User.query.filter_by(username='epi').first()
            
            # If user doesn't exist, create it
            if not user:
                user = User(username='epi', role='cashier')
                user.set_password('Epi@654')
                db.session.add(user)
                db.session.commit()
                logger.info("Created cashier user 'epi'")
            
            # Log the user in
            login_user(user)
            logger.info("User 'epi' logged in successfully")
            
            # Redirect directly to cashier dashboard using absolute URL to avoid loops
            return redirect('/cashier/dashboard', code=303)
        except Exception as e:
            logger.error(f"Error in cashier login: {str(e)}", exc_info=True)
            # Return a simple error message
            return f"<html><body><h1>Login Error</h1><p>An error occurred during login.</p><p>Error details: {str(e)}</p><p><a href='/login'>Try Again</a></p></body></html>"
    
    # Standard login flow for other users
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        # Log the user in
        login_user(user)
        
        # Log successful login
        logger.info(f"User {username} with role {user.role} logged in successfully")
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'cashier':
            # Use direct URL with 303 code to avoid redirect loops
            return redirect('/cashier/dashboard', code=303)
        else:
            flash(_('Invalid user role'), 'danger')
            return render_template('login.html')
    else:
        flash(_('Invalid username or password'), 'danger')
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    try:
        if current_user.role != 'admin':
            flash(_('Access denied. Admin privileges required.'), 'danger')
            return redirect(url_for('index'))
        
        # Get today's date in Central Africa Time (CAT, GMT+2)
        cat = pytz.timezone('Africa/Johannesburg')
        today = datetime.now(cat).date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get counts and product data
        try:
            # Get product counts
            total_products = Product.query.count()
            low_stock_count = Product.query.filter(Product.stock <= Product.low_stock_threshold).count()
            out_of_stock_products = Product.query.filter(Product.stock == 0).count()
            
            # Get all products for category statistics
            all_products = Product.query.all()
            
            # Get low stock products as a list (not just count)
            low_stock_items = Product.query.filter(
                Product.stock <= Product.low_stock_threshold,
                Product.stock > 0
            ).all()
        except Exception as e:
            logger.error(f"Error getting product counts: {str(e)}")
            total_products = 0
            low_stock_count = 0
            out_of_stock_products = 0
            all_products = []
            low_stock_items = []
        
        # Get today's sales
        try:
            today_sales = Sale.query.filter(
                db.func.date(Sale.date_sold) == today.strftime('%Y-%m-%d')
            ).all()
            today_sales_count = len(today_sales)
            
            # Handle case where purchase_price might be None
            total_revenue = sum(sale.total_price for sale in today_sales)
            
            # Calculate profit with error handling for each sale
            total_profit = 0
            for sale in today_sales:
                try:
                    purchase_price = sale.product.purchase_price or 0
                    profit = sale.total_price - (purchase_price * sale.quantity)
                    total_profit += profit
                except Exception as e:
                    logger.error(f"Error calculating profit for sale {sale.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting today's sales: {str(e)}")
            today_sales = []
            today_sales_count = 0
            total_revenue = 0
            total_profit = 0
        
        # Get recent sales
        try:
            recent_sales = Sale.query.order_by(Sale.date_sold.desc()).limit(5).all()
        except Exception as e:
            logger.error(f"Error getting recent sales: {str(e)}")
            recent_sales = []
        
        # Get latest monthly profit data
        try:
            # First check if the table exists to prevent the 'int' object is not iterable error
            try:
                db.session.execute(db.text("SELECT 1 FROM monthly_profit LIMIT 1"))
                table_exists = True
            except Exception as e:
                if 'no such table' in str(e).lower():
                    logger.warning("monthly_profit table does not exist")
                    table_exists = False
                else:
                    raise
            
            if table_exists:
                latest_monthly_profit = MonthlyProfit.query.order_by(
                    MonthlyProfit.year.desc(), 
                    MonthlyProfit.month.desc()
                ).first()
                
                # Get current month's profit data
                current_month = today.month
                current_year = today.year
                current_month_profit = MonthlyProfit.query.filter_by(
                    year=current_year, 
                    month=current_month
                ).first()
                
                # Calculate month-to-date profit if current month data exists
                if current_month_profit:
                    month_to_date_profit = current_month_profit.total_profit
                    month_to_date_revenue = current_month_profit.total_revenue
                else:
                    month_to_date_profit = 0
                    month_to_date_revenue = 0
            else:
                # Create a dummy object if the table doesn't exist
                class DummyProfit:
                    def __init__(self):
                        self.year = today.year
                        self.month = today.month
                        self.total_revenue = 0
                        self.total_cost = 0
                        self.total_profit = 0
                        self.sale_count = 0
                
                latest_monthly_profit = DummyProfit()
                month_to_date_profit = 0
                month_to_date_revenue = 0
        except Exception as e:
            logger.error(f"Error getting monthly profit data: {str(e)}")
            latest_monthly_profit = None
            month_to_date_profit = 0
            month_to_date_revenue = 0
        
        return render_template('admin_dashboard.html', 
                               total_products=total_products,
                               low_stock_count=low_stock_count,
                               low_stock_products=low_stock_items,  # Pass the list of products, not just the count
                               out_of_stock_products=out_of_stock_products,
                               today_sales_count=today_sales_count,
                               total_revenue=total_revenue,
                               total_profit=total_profit,
                               recent_sales=recent_sales,
                               products=all_products,  # Pass all products for category statistics
                               latest_monthly_profit=latest_monthly_profit,
                               month_to_date_profit=month_to_date_profit,
                               month_to_date_revenue=month_to_date_revenue,
                               today=today)  # Pass today's date to the template
    except Exception as e:
        logger.error(f"Unhandled error in admin_dashboard: {str(e)}")
        flash(_('An error occurred while loading the dashboard. Please try again.'), 'danger')
        return redirect(url_for('index'))

@app.route('/admin/products', methods=['GET'])
@login_required
def manage_products():
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '')
    
    if search_query:
        # Search in name, description, and category fields
        search_term = f'%{search_query}%'
        products = Product.query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.category.ilike(search_term)
            )
        ).order_by(Product.name).all()
    else:
        products = Product.query.order_by(Product.name).all()
    
    return render_template('manage_products.html', products=products, search_query=search_query)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        purchase_price = float(request.form.get('purchase_price', 0))
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        low_stock_threshold = int(request.form.get('low_stock_threshold'))
        is_packaged = request.form.get('is_packaged') == 'on'
        units_per_package = int(request.form.get('units_per_package', 1))
        individual_price = float(request.form.get('individual_price', 0))
        individual_stock = int(request.form.get('individual_stock', 0))
        
        product = Product(
            name=name,
            description=description,
            category=category,
            purchase_price=purchase_price,
            price=price,
            stock=stock,
            low_stock_threshold=low_stock_threshold,
            is_packaged=is_packaged,
            units_per_package=units_per_package,
            individual_price=individual_price,
            individual_stock=individual_stock
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(_('Product added successfully!'), 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('add_product.html')

@app.route('/cashier/dashboard')
@login_required
def cashier_dashboard():
    try:
        logger.info(f"Cashier dashboard accessed by user: {current_user.username}, role: {current_user.role}")
        
        # Don't redirect if role doesn't match, just show the dashboard anyway
        # This prevents redirect loops between login and dashboard
        if current_user.role != 'cashier':
            logger.warning(f"Non-cashier accessing cashier dashboard: {current_user.username}, role: {current_user.role}")
            flash(_('Note: You are viewing the cashier dashboard but have a different role.'), 'warning')
        
        # Get today's date
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get search query with error handling
        try:
            search_query = request.args.get('search', '')
        except Exception as e:
            logger.error(f"Error getting search query: {str(e)}")
            search_query = ''
        
        # Get products in stock with optional search filter
        try:
            products_query = Product.query.filter(Product.stock > 0)
            
            # Apply search filter if provided
            if search_query and search_query.strip():
                search_term = "%" + search_query + "%"
                products_query = products_query.filter(Product.name.like(search_term))
            
            # Execute query
            products = products_query.all()
        except Exception as e:
            logger.error(f"Error in product search: {str(e)}")
            products = []
        
        # Get today's sales for this cashier
        try:
            today_sales = Sale.query.filter(
                Sale.date_sold.between(today_start, today_end),
                Sale.cashier_id == current_user.id
            ).all()
            
            # Calculate total revenue for today
            total_revenue = sum(sale.total_price for sale in today_sales)
        except Exception as e:
            logger.error(f"Error getting sales: {str(e)}")
            today_sales = []
            total_revenue = 0
        
        return render_template('cashier_dashboard.html', 
                            products=products or [],
                            today_sales=today_sales or [],
                            total_revenue=total_revenue or 0,
                            search_query=search_query or '')
    except Exception as e:
        logger.error(f"Error in cashier_dashboard: {str(e)}", exc_info=True)
        flash(_('An error occurred while loading the cashier dashboard.'), 'danger')
        # Fallback to a simple message instead of using a template that might not exist
        return f"<html><body><h1>Error</h1><p>An error occurred while loading the cashier dashboard.</p><p>Error details: {str(e)}</p><p><a href='/'>Go to Home</a></p></body></html>"

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.purchase_price = float(request.form.get('purchase_price', 0))
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.low_stock_threshold = int(request.form.get('low_stock_threshold'))
        product.is_packaged = request.form.get('is_packaged') == 'on'
        product.units_per_package = int(request.form.get('units_per_package', 1))
        product.individual_price = float(request.form.get('individual_price', 0))
        product.individual_stock = int(request.form.get('individual_stock', 0))
        
        db.session.commit()
        
        flash(_('Product updated successfully!'), 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Check if product has associated sales
    if Sale.query.filter_by(product_id=product_id).first():
        flash(_('Cannot delete product "{0}" because it has associated sales records. Consider updating the product instead.', product.name), 'danger')
        return redirect(url_for('manage_products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash(_('Product deleted successfully!'), 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/sales')
@login_required
def view_sales():
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    # Get query parameters
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    category = request.args.get('category', '')
    cashier_id = request.args.get('cashier_id', '')
    
    # Parse dates
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_datetime = datetime.combine(start_date, datetime.min.time())
        else:
            # Default to today (using CAT timezone)
            cat_timezone = pytz.timezone('Africa/Kigali')
            today = datetime.now(cat_timezone).date()
            start_date = today
            start_datetime = cat_timezone.localize(datetime.combine(start_date, datetime.min.time()))
            start_date_str = start_date.strftime('%Y-%m-%d')
            
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_datetime = datetime.combine(end_date, datetime.max.time())
        else:
            # Default to today (using CAT timezone)
            cat_timezone = pytz.timezone('Africa/Kigali')
            today = datetime.now(cat_timezone).date()
            end_date = today
            end_datetime = cat_timezone.localize(datetime.combine(end_date, datetime.max.time()))
            end_date_str = end_date.strftime('%Y-%m-%d')
    except ValueError:
        flash(_('Invalid date format. Please use YYYY-MM-DD.'), 'danger')
        return redirect(url_for('view_sales'))
    
    # Build query - use string-based date comparison for better timezone handling
    if start_date == end_date:
        # If viewing a single day, use the more reliable date function
        logger.debug(f"Filtering admin sales view for single date: {start_date_str}")
        query = Sale.query.filter(db.func.date(Sale.date_sold) == start_date_str)
    else:
        # For date ranges, use between
        logger.debug(f"Filtering admin sales view from {start_date_str} to {end_date_str}")
        query = Sale.query.filter(Sale.date_sold.between(start_datetime, end_datetime))
    
    if category and category != 'all':
        query = query.join(Product).filter(Product.category == category)
        
    if cashier_id and cashier_id.isdigit():
        query = query.filter(Sale.cashier_id == int(cashier_id))
    
    # Execute query
    sales = query.order_by(Sale.date_sold.desc()).all()
    
    # Calculate total revenue
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Calculate total profit
    total_profit = sum((sale.total_price - (sale.product.purchase_price * sale.quantity)) for sale in sales)
    
    # Get all cashiers for the filter dropdown
    cashiers = User.query.filter_by(role='cashier').all()
    
    # Get all product categories for the filter dropdown
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories]
    
    # Calculate sales by category
    category_summary = {}
    for sale in sales:
        category = sale.product.category
        if category not in category_summary:
            category_summary[category] = {
                'count': 0,
                'revenue': 0,
                'profit': 0
            }
        category_summary[category]['count'] += sale.quantity
        category_summary[category]['revenue'] += sale.total_price
        category_summary[category]['profit'] += (sale.total_price - (sale.product.purchase_price * sale.quantity))
    
    return render_template('view_sales.html', 
                           sales=sales, 
                           total_revenue=total_revenue,
                           total_profit=total_profit,
                           categories=categories,
                           category_summary=category_summary,
                           selected_category=category,
                           cashiers=cashiers,
                           selected_cashier_id=cashier_id,
                           start_date=start_date_str,
                           end_date=end_date_str)

@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    sale = Sale.query.get_or_404(sale_id)
    
    # Return the stock to the product
    product = sale.product
    product.stock += sale.quantity
    
    # Store sale info for flash message
    product_name = sale.product.name
    quantity = sale.quantity
    sale_date = sale.date_sold.strftime('%Y-%m-%d %H:%M')
    cashier_name = sale.cashier.username
    
    # Delete the sale
    db.session.delete(sale)
    db.session.commit()
    
    flash(_('Sale of %(quantity)d %(product)s by %(cashier)s on %(date)s has been deleted and stock has been restored.', 
            quantity=quantity, product=product_name, cashier=cashier_name, date=sale_date), 'success')
    
    return redirect(url_for('view_sales'))

# Second cashier_dashboard route removed to avoid duplicate endpoint error

@app.route('/cashier/sell', methods=['GET', 'POST'])
@app.route('/sell_product', methods=['GET', 'POST'])
@app.route('/record_sale', methods=['GET', 'POST'])
@login_required
def sell_product():
    try:
        if current_user.role != 'cashier':
            flash(_('Access denied. Cashier privileges required.'), 'danger')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                # Get form data with validation
                product_id = request.form.get('product_id')
                if not product_id:
                    flash(_('Please select a product.'), 'danger')
                    return redirect(url_for('cashier_dashboard'))
                
                try:
                    quantity = int(request.form.get('quantity', 1))
                    if quantity <= 0:
                        raise ValueError("Quantity must be positive")
                except ValueError:
                    flash(_('Please enter a valid quantity.'), 'danger')
                    return redirect(url_for('cashier_dashboard'))
                
                sale_type = request.form.get('sale_type', 'package')  # Default to package if not specified
                
                # Log the sale attempt for debugging
                logger.debug(f"Sale attempt: product_id={product_id}, quantity={quantity}, sale_type={sale_type}")
                
                # Get the product
                product = Product.query.get(product_id)
                if not product:
                    flash(_('Product not found.'), 'danger')
                    return redirect(url_for('cashier_dashboard'))
                
                # Handle packaged products differently based on sale type
                if product.is_packaged:
                    if sale_type == 'package':
                        # Selling complete packages
                        if product.stock < quantity:
                            flash(_('Not enough packages available. Only {0} packages left.', product.stock), 'danger')
                            return redirect(url_for('cashier_dashboard'))
                        
                        # Calculate total price for packages
                        total_price = product.price * quantity
                        
                        # Update package stock
                        product.stock -= quantity
                    else:
                        # Selling individual units
                        if product.individual_stock < quantity:
                            flash(_('Not enough individual units available. Only {0} units left.', product.individual_stock), 'danger')
                            return redirect(url_for('cashier_dashboard'))
                        
                        # Calculate total price for individual units
                        total_price = product.individual_price * quantity
                        
                        # Update individual stock
                        product.individual_stock -= quantity
                else:
                    # Regular non-packaged product
                    if product.stock < quantity:
                        flash(_('Not enough stock available. Only {0} units left.', product.stock), 'danger')
                        return redirect(url_for('cashier_dashboard'))
                    
                    # Calculate total price
                    total_price = product.price * quantity
                    
                    # Update product stock
                    product.stock -= quantity
                
                # Create sale record with explicit CAT timezone
                cat_now = get_cat_time()
                logger.debug(f"Recording sale with CAT timezone: {cat_now}")
                
                sale = Sale(
                    product_id=product_id,
                    quantity=quantity,
                    total_price=total_price,
                    cashier_id=current_user.id,
                    date_sold=cat_now
                )
                
                # Add and commit the changes to the database
                try:
                    db.session.add(sale)
                    db.session.commit()
                    logger.debug(f"Sale recorded successfully: id={sale.id}, product={product.name}, quantity={quantity}, total_price={total_price}")
                    
                    # Update monthly profit data
                    try:
                        update_monthly_profit(sale)
                    except Exception as e:
                        logger.error(f"Error updating monthly profit: {str(e)}")
                        # Continue even if monthly profit update fails
                    
                    flash(_('Sale recorded successfully!'), 'success')
                    return redirect(url_for('cashier_dashboard'))
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Database error recording sale: {str(db_error)}")
                    flash(_('Error recording sale. Please try again.'), 'danger')
                    return redirect(url_for('cashier_dashboard'))
            
            except Exception as form_error:
                logger.error(f"Error processing sale form: {str(form_error)}")
                flash(_('Error processing sale. Please try again.'), 'danger')
                return redirect(url_for('cashier_dashboard'))
        
        # If GET request, redirect to cashier dashboard
        return redirect(url_for('cashier_dashboard'))
    
    except Exception as e:
        logger.error(f"Unhandled error in sell_product: {str(e)}")
        flash(_('An unexpected error occurred. Please try again.'), 'danger')
        return redirect(url_for('cashier_dashboard'))

@app.route('/cashier/sales')
@login_required
def view_cashier_sales():
    # Restrict cashiers from accessing sales history - they should only see current day's sales on dashboard
    if current_user.role == 'cashier':
        flash(_('Access restricted. Cashiers can only view current day\'s sales on the dashboard.'), 'warning')
        return redirect(url_for('cashier_dashboard'))
    
    # Only admins should be able to access this page
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    category = request.args.get('category')
    
    # If no date filters provided, default to today's sales
    if not start_date_str and not end_date_str:
        # Get today's date in CAT timezone
        cat_timezone = pytz.timezone('Africa/Kigali')
        today = datetime.now(cat_timezone).date()
        start_date_str = today.strftime('%Y-%m-%d')
        end_date_str = today.strftime('%Y-%m-%d')
    
    # Base query - only show sales by the current cashier
    query = Sale.query.filter(Sale.cashier_id == current_user.id)
    
    # Apply date filters if provided
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Sale.date_sold >= start_date)
        except ValueError:
            flash(_('Invalid start date format. Please use YYYY-MM-DD.'), 'warning')
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Add one day to include the end date
            end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            query = query.filter(Sale.date_sold <= end_date)
        except ValueError:
            flash(_('Invalid end date format. Please use YYYY-MM-DD.'), 'warning')
    
    # Apply category filter if provided
    if category and category != 'all':
        query = query.join(Product).filter(Product.category == category)
    
    # Get all sales based on the filters
    sales = query.order_by(Sale.date_sold.desc()).all()
    
    # Calculate total revenue
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Get unique categories for the filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    # Group sales by category for the summary
    category_summary = {}
    for sale in sales:
        category = sale.product.category
        if category not in category_summary:
            category_summary[category] = {
                'count': 0,
                'revenue': 0
            }
        category_summary[category]['count'] += sale.quantity
        category_summary[category]['revenue'] += sale.total_price
    
    return render_template('cashier_sales.html', 
                           sales=sales, 
                           total_revenue=total_revenue,
                           categories=categories,
                           category_summary=category_summary,
                           selected_category=category,
                           start_date=start_date_str,
                           end_date=end_date_str)

# Initialize the database and create an admin user
@app.cli.command('init-db')
def init_db_command():
    """Initialize the database and create admin and cashier users if they don't exist."""
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Created admin user with username: admin and password: admin123')
    else:
        print('Admin user already exists')
    
    # Check if cashier user exists
    cashier = User.query.filter_by(username='cashier').first()
    if not cashier:
        cashier = User(username='cashier', role='cashier')
        cashier.set_password('cashier123')
        db.session.add(cashier)
        db.session.commit()
        print('Created cashier user with username: cashier and password: cashier123')
    else:
        print('Cashier user already exists')

# Function to update monthly profit data when a sale is made
def update_monthly_profit(sale):
    """Update monthly profit data when a sale is made"""
    try:
        # Ensure the monthly_profit table exists
        try:
            db.session.execute(db.text("SELECT 1 FROM monthly_profit LIMIT 1"))
        except Exception as e:
            if 'no such table' in str(e).lower():
                logger.warning("monthly_profit table does not exist, creating it now")
                with app.app_context():
                    db.create_all()
            else:
                logger.error(f"Database error checking for monthly_profit table: {str(e)}")
                raise
        
        # Get the year and month from the sale date
        year = sale.date_sold.year
        month = sale.date_sold.month
        
        # Calculate the profit for this sale
        purchase_price = sale.product.purchase_price or 0
        cost = purchase_price * sale.quantity
        profit = sale.total_price - cost
        
        # Find or create the monthly profit record
        monthly_profit = MonthlyProfit.query.filter_by(year=year, month=month).first()
        
        if monthly_profit:
            # Update existing record
            monthly_profit.total_revenue += sale.total_price
            monthly_profit.total_cost += cost
            monthly_profit.total_profit += profit
            monthly_profit.sale_count += 1
        else:
            # Create new record
            monthly_profit = MonthlyProfit(
                year=year,
                month=month,
                total_revenue=sale.total_price,
                total_cost=cost,
                total_profit=profit,
                sale_count=1
            )
            db.session.add(monthly_profit)
        
        db.session.commit()
        logger.info(f"Updated monthly profit for {year}-{month}")
    except Exception as e:
        logger.error(f"Error updating monthly profit: {str(e)}")
        db.session.rollback()

# Function to recalculate all monthly profits from sales data
def recalculate_monthly_profits(start_day=1):
    try:
        # Validate start_day
        if not isinstance(start_day, int) or start_day < 1 or start_day > 28:
            start_day = 1  # Default to 1 if invalid
            
        logger.debug(f"Recalculating monthly profits with accounting period starting on day {start_day}")
        
        # Clear existing monthly profit data
        MonthlyProfit.query.delete()
        db.session.commit()
        
        # Get all sales ordered by date
        sales = Sale.query.order_by(Sale.date_sold).all()
        
        if not sales:
            logger.info("No sales found to calculate profits from")
            return True
            
        # Group sales by accounting periods based on start_day
        # For example, if start_day is 15, periods are from 15th to 14th of next month
        accounting_periods = {}
        
        for sale in sales:
            sale_date = sale.date_sold.date()
            # Determine the accounting period this sale belongs to
            if sale_date.day >= start_day:
                # This sale belongs to the current month's period
                period_year = sale_date.year
                period_month = sale_date.month
            else:
                # This sale belongs to the previous month's period
                # Adjust for January (month 1)
                if sale_date.month == 1:
                    period_year = sale_date.year - 1
                    period_month = 12
                else:
                    period_year = sale_date.year
                    period_month = sale_date.month - 1
                    
            period_key = (period_year, period_month)
            
            if period_key not in accounting_periods:
                accounting_periods[period_key] = []
                
            accounting_periods[period_key].append(sale)
        
        # Process each accounting period
        for (year, month), period_sales in accounting_periods.items():
            # Calculate totals for this period
            total_revenue = 0
            total_cost = 0
            total_profit = 0
            sale_count = 0
            
            for sale in period_sales:
                # Calculate profit for this sale
                purchase_price = sale.product.purchase_price or 0
                cost = purchase_price * sale.quantity
                profit = sale.total_price - cost
                
                # Add to period totals
                total_revenue += sale.total_price
                total_cost += cost
                total_profit += profit
                sale_count += 1
            
            # Create monthly profit record for this period
            monthly_profit = MonthlyProfit(
                year=year,
                month=month,
                total_revenue=total_revenue,
                total_cost=total_cost,
                total_profit=total_profit,
                sale_count=sale_count
            )
            db.session.add(monthly_profit)
        
        db.session.commit()
        logger.info(f"Successfully recalculated all monthly profits with start day {start_day}")
        return True
    except Exception as e:
        logger.error(f"Error recalculating monthly profits: {str(e)}")
        db.session.rollback()
        return False

@app.route('/admin/monthly-profits')
@app.route('/admin/monthly_profits')  # Add underscore version for compatibility
@login_required
def view_monthly_profits():
    try:
        if current_user.role != 'admin':
            flash(_('Access denied. Admin privileges required.'), 'danger')
            return redirect(url_for('index'))
        
        # Get the start day from query parameters, default to 1
        start_day = request.args.get('start_day', '1')
        try:
            start_day = int(start_day)
            if start_day < 1 or start_day > 28:
                start_day = 1  # Default to 1 if invalid
        except (ValueError, TypeError):
            start_day = 1
        
        # Define possible start days (1-28)
        start_days = list(range(1, 29))
        
        # First check if the table exists
        try:
            db.session.execute(db.text("SELECT 1 FROM monthly_profit LIMIT 1"))
            table_exists = True
        except Exception as e:
            if 'no such table' in str(e).lower():
                logger.warning("monthly_profit table does not exist, creating it now")
                table_exists = False
                # Create the table if it doesn't exist
                with app.app_context():
                    db.create_all()
                # Try to recalculate profits
                recalculate_monthly_profits(start_day=start_day)
            else:
                logger.error(f"Database error checking for monthly_profit table: {str(e)}")
                raise
        
        # Get all monthly profit records ordered by year and month (most recent first)
        monthly_profits = MonthlyProfit.query.order_by(MonthlyProfit.year.desc(), MonthlyProfit.month.desc()).all()
        
        # Calculate totals
        total_revenue = sum(mp.total_revenue for mp in monthly_profits)
        total_cost = sum(mp.total_cost for mp in monthly_profits)
        total_profit = sum(mp.total_profit for mp in monthly_profits)
        total_sales = sum(mp.sale_count for mp in monthly_profits)
        
        # Calculate average monthly profit
        avg_monthly_profit = total_profit / len(monthly_profits) if monthly_profits else 0
        
        # Get month names for display
        month_names = [
            _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
            _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
        ]
        
        logger.debug(f"Rendering monthly_profits.html with current_start_day={start_day}")
        
        return render_template(
            'monthly_profits.html',
            monthly_profits=monthly_profits,
            month_names=month_names,
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            total_sales=total_sales,
            avg_monthly_profit=avg_monthly_profit,
            start_days=start_days,
            current_start_day=start_day
        )
    except Exception as e:
        logger.error(f"Error in view_monthly_profits: {str(e)}", exc_info=True)
        flash(_('An error occurred while loading the monthly profits. Please try again.'), 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/recalculate_profits', methods=['POST'])
@login_required
def admin_recalculate_profits():
    try:
        if current_user.role != 'admin':
            flash(_('Access denied. Admin privileges required.'), 'danger')
            return redirect(url_for('index'))
        
        # Get the start day from the form
        start_day = request.form.get('start_day', '1')
        try:
            start_day = int(start_day)
            if start_day < 1 or start_day > 28:
                start_day = 1  # Default to 1 if invalid
        except (ValueError, TypeError):
            start_day = 1
        
        logger.debug(f"Recalculating monthly profits with start_day={start_day}")
        
        if recalculate_monthly_profits(start_day=start_day):
            flash(_('Monthly profits have been recalculated successfully.'), 'success')
        else:
            flash(_('An error occurred while recalculating monthly profits.'), 'danger')
        
        # Return to the monthly profits page with the same start day
        return redirect(url_for('view_monthly_profits', start_day=start_day))
    except Exception as e:
        logger.error(f"Error in admin_recalculate_profits: {str(e)}")
        flash(_('An error occurred while recalculating profits. Please try again.'), 'danger')
        return redirect(url_for('view_monthly_profits'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
