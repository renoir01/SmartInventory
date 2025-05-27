from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)

class MonthlyProfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    start_day = db.Column(db.Integer, default=1)  # Default to 1st day of month
    end_day = db.Column(db.Integer, default=31)  # Default to last day of month
    total_revenue = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    sale_count = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('year', 'month', 'start_day', name='unique_year_month_start'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cashier_dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        # Break potential redirect loops by going directly to login template
        return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        # Don't redirect if already authenticated to avoid loops
        # Instead, check role and render appropriate dashboard
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cashier_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('cashier_dashboard'))
            else:
                flash(_('Invalid username or password'), 'danger')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
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
        
        # Get today's date
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get counts
        try:
            total_products = Product.query.count()
            low_stock_products = Product.query.filter(Product.stock <= Product.low_stock_threshold).count()
            out_of_stock_products = Product.query.filter(Product.stock == 0).count()
        except Exception as e:
            logger.error(f"Error getting product counts: {str(e)}")
            total_products = 0
            low_stock_products = 0
            out_of_stock_products = 0
        
        # Get today's sales
        try:
            today_sales = Sale.query.filter(Sale.date_sold.between(today_start, today_end)).all()
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
        
        # Get low stock products
        try:
            low_stock_items = Product.query.filter(
                Product.stock <= Product.low_stock_threshold,
                Product.stock > 0
            ).all()
        except Exception as e:
            logger.error(f"Error getting low stock items: {str(e)}")
            low_stock_items = []
        
        # Create a dummy profit object as a fallback
        class DummyProfit:
            def __init__(self):
                self.year = today.year
                self.month = today.month
                self.total_revenue = 0
                self.total_cost = 0
                self.total_profit = 0
                self.sale_count = 0
        
        # Default values
        latest_monthly_profit = DummyProfit()
        month_to_date_profit = 0
        month_to_date_revenue = 0
        
        # Try to get monthly profit data with extensive error handling
        try:
            # First check if the table exists
            table_exists = False
            try:
                result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'"))
                table_exists = bool(result.scalar())
            except Exception as e:
                logger.error(f"Error checking if monthly_profit table exists: {str(e)}")
                table_exists = False
            
            if table_exists:
                try:
                    # Get the latest monthly profit record
                    latest_mp_query = db.text(
                        "SELECT id, year, month, total_revenue, total_cost, total_profit, sale_count "
                        "FROM monthly_profit ORDER BY year DESC, month DESC LIMIT 1"
                    )
                    latest_mp_result = db.session.execute(latest_mp_query).fetchone()
                    
                    if latest_mp_result:
                        try:
                            # Safely extract values with type checking
                            latest_monthly_profit.year = int(latest_mp_result.year) if latest_mp_result.year is not None else today.year
                            latest_monthly_profit.month = int(latest_mp_result.month) if latest_mp_result.month is not None else today.month
                            latest_monthly_profit.total_revenue = float(latest_mp_result.total_revenue) if latest_mp_result.total_revenue is not None else 0.0
                            latest_monthly_profit.total_cost = float(latest_mp_result.total_cost) if latest_mp_result.total_cost is not None else 0.0
                            latest_monthly_profit.total_profit = float(latest_mp_result.total_profit) if latest_mp_result.total_profit is not None else 0.0
                            latest_monthly_profit.sale_count = int(latest_mp_result.sale_count) if latest_mp_result.sale_count is not None else 0
                        except (TypeError, ValueError) as e:
                            logger.error(f"Error converting monthly profit data types: {str(e)}")
                            # Keep using the default values
                except Exception as e:
                    logger.error(f"Error getting latest monthly profit: {str(e)}")
                
                try:
                    # Get current month data with explicit type conversion
                    current_month = today.month
                    current_year = today.year
                    current_mp_query = db.text(
                        "SELECT total_revenue, total_profit FROM monthly_profit "
                        "WHERE year = :year AND month = :month"
                    )
                    current_mp_result = db.session.execute(current_mp_query, {"year": current_year, "month": current_month}).fetchone()
                    
                    if current_mp_result:
                        try:
                            month_to_date_revenue = float(current_mp_result.total_revenue) if current_mp_result.total_revenue is not None else 0.0
                            month_to_date_profit = float(current_mp_result.total_profit) if current_mp_result.total_profit is not None else 0.0
                        except (TypeError, ValueError) as e:
                            logger.error(f"Error converting current month data types: {str(e)}")
                            # Keep using the default values
                except Exception as e:
                    logger.error(f"Error getting current month profit: {str(e)}")
        except Exception as e:
            logger.error(f"Unhandled error in monthly profit processing: {str(e)}")
            # Keep using the default values
        
        return render_template('admin_dashboard.html', 
                               total_products=total_products,
                               low_stock_products=low_stock_products,
                               out_of_stock_products=out_of_stock_products,
                               today_sales_count=today_sales_count,
                               total_revenue=total_revenue,
                               total_profit=total_profit,
                               recent_sales=recent_sales,
                               low_stock_items=low_stock_items,
                               latest_monthly_profit=latest_monthly_profit,
                               month_to_date_profit=month_to_date_profit,
                               month_to_date_revenue=month_to_date_revenue)
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
            # Default to beginning of current month
            today = datetime.now().date()
            start_date = datetime(today.year, today.month, 1).date()
            start_datetime = datetime.combine(start_date, datetime.min.time())
            start_date_str = start_date.strftime('%Y-%m-%d')
            
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_datetime = datetime.combine(end_date, datetime.max.time())
        else:
            # Default to today
            end_date = datetime.now().date()
            end_datetime = datetime.combine(end_date, datetime.max.time())
            end_date_str = end_date.strftime('%Y-%m-%d')
    except ValueError:
        flash(_('Invalid date format. Please use YYYY-MM-DD.'), 'danger')
        return redirect(url_for('view_sales'))
    
    # Build query
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

@app.route('/cashier/dashboard')
@login_required
def cashier_dashboard():
    try:
        if current_user.role != 'cashier':
            flash(_('Access denied. Cashier privileges required.'), 'danger')
            return redirect(url_for('index'))
        
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
            products = Product.query.filter(Product.stock > 0).all()
        
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
                            products=products,
                            today_sales=today_sales,
                            total_revenue=total_revenue,
                            search_query=search_query)
    except Exception as e:
        logger.error(f"Unhandled error in cashier_dashboard: {str(e)}")
        flash(_('An error occurred. Please try again.'), 'danger')
        return redirect(url_for('index'))

@app.route('/cashier/sell', methods=['GET', 'POST'])
@login_required
def sell_product():
    if current_user.role != 'cashier':
        flash(_('Access denied. Cashier privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        sale_type = request.form.get('sale_type', 'package')  # Default to package if not specified
        
        product = Product.query.get_or_404(product_id)
        
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
        
        # Create sale record
        sale = Sale(
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            cashier_id=current_user.id
        )
        
        db.session.add(sale)
        db.session.commit()
        
        # Update monthly profit data
        update_monthly_profit(sale)
        
        flash(_('Sale recorded successfully!'), 'success')
        return redirect(url_for('cashier_dashboard'))
    
    # If GET request, redirect to cashier dashboard
    return redirect(url_for('cashier_dashboard'))

@app.route('/cashier/sales')
@login_required
def view_cashier_sales():
    if current_user.role != 'cashier':
        flash(_('Access denied. Cashier privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    category = request.args.get('category')
    
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
def init_db_command():
    """Initialize the database and create admin and cashier users if they don't exist."""
    print("Creating database tables...")
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("Created admin user with username 'admin' and password 'admin123'")
    else:
        print("Admin user already exists.")
    
    # Check if cashier user exists
    cashier = User.query.filter_by(username='cashier').first()
    if not cashier:
        cashier = User(username='cashier', role='cashier')
        cashier.set_password('cashier123')
        db.session.add(cashier)
        print("Created cashier user with username 'cashier' and password 'cashier123'")
    else:
        print("Cashier user already exists.")
    
    db.session.commit()
    print("Database initialization complete.")
    
    return True

# Function to update monthly profit data when a sale is made
def update_monthly_profit(sale):
    try:
        # Get the year and month from the sale date
        year = sale.date_sold.year
        month = sale.date_sold.month
        
        # Calculate the profit for this sale
        purchase_price = sale.product.purchase_price or 0
        cost = purchase_price * sale.quantity
        profit = sale.total_price - cost
        
        # Find or create the monthly profit record
        monthly_profit = MonthlyProfit.query.filter_by(year=year, month=month, start_day=1).first()
        
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
        # Clear existing monthly profit data
        MonthlyProfit.query.delete()
        db.session.commit()
        
        # Get all sales ordered by date
        sales = Sale.query.order_by(Sale.date_sold).all()
        
        # Group sales by custom month periods
        if start_day == 1:
            # Standard calendar month
            for sale in sales:
                update_monthly_profit(sale)
        else:
            # Custom period (e.g., 12th to 12th)
            # First, clear any existing data
            MonthlyProfit.query.delete()
            db.session.commit()
            
            # Group sales by custom periods
            from collections import defaultdict
            from calendar import monthrange
            
            # Dictionary to store aggregated data by period
            periods = defaultdict(lambda: {'revenue': 0, 'cost': 0, 'profit': 0, 'count': 0})
            
            for sale in sales:
                sale_day = sale.date_sold.day
                sale_month = sale.date_sold.month
                sale_year = sale.date_sold.year
                
                # Determine which period this sale belongs to
                if sale_day >= start_day:
                    # This belongs to the current month's period
                    period_key = (sale_year, sale_month, start_day)
                else:
                    # This belongs to the previous month's period
                    # Calculate previous month and year
                    if sale_month == 1:
                        prev_month = 12
                        prev_year = sale_year - 1
                    else:
                        prev_month = sale_month - 1
                        prev_year = sale_year
                    
                    period_key = (prev_year, prev_month, start_day)
                
                # Calculate profit for this sale
                purchase_price = sale.product.purchase_price or 0
                cost = purchase_price * sale.quantity
                profit = sale.total_price - cost
                
                # Add to the appropriate period
                periods[period_key]['revenue'] += sale.total_price
                periods[period_key]['cost'] += cost
                periods[period_key]['profit'] += profit
                periods[period_key]['count'] += 1
            
            # Create monthly profit records from the aggregated data
            for period_key, data in periods.items():
                year, month, day = period_key
                
                # Calculate end day (day before start_day of next month)
                if start_day == 1:
                    # If starting on the 1st, end on the last day of the month
                    _, last_day = monthrange(year, month)
                    end_day = last_day
                else:
                    # Otherwise, end on the day before start_day of next month
                    next_month = month + 1 if month < 12 else 1
                    next_year = year if month < 12 else year + 1
                    end_day = start_day - 1
                    
                    # Handle case where end_day would be 0
                    if end_day == 0:
                        # Go to previous month's last day
                        if month == 1:
                            prev_month = 12
                            prev_year = year - 1
                        else:
                            prev_month = month - 1
                            prev_year = year
                        _, end_day = monthrange(prev_year, prev_month)
                
                # Create the monthly profit record
                monthly_profit = MonthlyProfit(
                    year=year,
                    month=month,
                    start_day=start_day,
                    end_day=end_day,
                    total_revenue=data['revenue'],
                    total_cost=data['cost'],
                    total_profit=data['profit'],
                    sale_count=data['count']
                )
                db.session.add(monthly_profit)
            
            db.session.commit()
            
        logger.info(f"Successfully recalculated all monthly profits with start day {start_day}")
        return True
    except Exception as e:
        logger.error(f"Error recalculating monthly profits: {str(e)}")
        db.session.rollback()
        return False

@app.route('/admin/monthly_profits')
@login_required
def view_monthly_profits():
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    # Get the start day from the query parameters (default to 1)
    try:
        start_day = int(request.args.get('start_day', 1))
        if start_day < 1 or start_day > 28:
            start_day = 1  # Default to 1 if invalid
    except (ValueError, TypeError):
        start_day = 1  # Default to 1 if there's an error
    
    # Get all monthly profit records ordered by year and month (most recent first)
    # Filter by start_day if specified
    query = MonthlyProfit.query
    if start_day != 1:
        query = query.filter_by(start_day=start_day)
    
    monthly_profits = query.order_by(MonthlyProfit.year.desc(), MonthlyProfit.month.desc()).all()
    
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
    
    # Generate a list of possible start days for the dropdown
    start_days = list(range(1, 29))  # 1 to 28 (all months have at least 28 days)
    
    return render_template(
        'monthly_profits.html',
        monthly_profits=monthly_profits,
        month_names=month_names,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_profit=total_profit,
        total_sales=total_sales,
        avg_monthly_profit=avg_monthly_profit,
        current_start_day=start_day,
        start_days=start_days
    )

@app.route('/admin/recalculate_profits', methods=['POST'])
@login_required
def admin_recalculate_profits():
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('index'))
    
    # Get the start day from the form
    try:
        start_day = int(request.form.get('start_day', 1))
        if start_day < 1 or start_day > 28:
            start_day = 1  # Default to 1 if invalid
    except (ValueError, TypeError):
        start_day = 1  # Default to 1 if there's an error
    
    if recalculate_monthly_profits(start_day):
        flash(_('Monthly profits recalculated successfully from day %(day)d!', day=start_day), 'success')
    else:
        flash(_('Error recalculating monthly profits. Please check the logs.'), 'danger')
    
    return redirect(url_for('view_monthly_profits'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
