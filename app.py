from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'emergency-fix-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = None  # Disable session protection temporarily

# Internationalization setup
try:
    from flask_babel import Babel, gettext as _

    def get_locale():
        return session.get('language', 'en')

    babel = Babel(app, locale_selector=get_locale)

    @app.route('/set_language/<language>')
    def set_language(language):
        session['language'] = language
        return redirect(request.referrer or url_for('index'))

    # Make the translation function available to templates
    @app.context_processor
    def inject_globals():
        return dict(_=_)

except ImportError:
    # Fallback translation function if Flask-Babel is not available
    def _(text, **variables):
        return text % variables if variables else text

    # Make the fallback translation function available to templates
    @app.context_processor
    def inject_globals():
        return dict(_=_)


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
    
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold
    
    def get_profit_margin(self):
        if self.purchase_price > 0:
            return ((self.price - self.purchase_price) / self.price) * 100
        return 100  # If purchase price is 0, profit margin is 100%

class Cashout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cashier = db.relationship('User', foreign_keys=[cashier_id], backref=db.backref('cashier_cashouts', lazy=True))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin = db.relationship('User', foreign_keys=[admin_id], backref=db.backref('admin_cashouts', lazy=True))
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(200), nullable=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('sales', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cashier = db.relationship('User', backref=db.backref('sales', lazy=True))
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)
    is_cashed_out = db.Column(db.Boolean, default=False)
    cashout_id = db.Column(db.Integer, db.ForeignKey('cashout.id'), nullable=True)
    cashout = db.relationship('Cashout', backref=db.backref('sales', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session
    session.clear()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cashier_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    # Get total products
    total_products = Product.query.count()
    
    # Get low stock products
    low_stock_products = Product.query.filter(Product.stock <= Product.low_stock_threshold).all()
    
    # Get all products for category summary
    products = Product.query.all()
    
    # Get today's date
    today = datetime.utcnow().date()
    
    # Get today's sales
    today_sales = Sale.query.filter(
        db.func.date(Sale.date_sold) == today
    ).all()
    
    today_sales_count = len(today_sales)
    today_revenue = sum(sale.total_price for sale in today_sales)
    
    # Calculate today's profit
    today_profit = 0
    for sale in today_sales:
        product = Product.query.get(sale.product_id)
        if product:
            profit_margin = product.get_profit_margin() / 100
            today_profit += sale.total_price * profit_margin
    
    # Get all-time sales data
    total_sales_count = Sale.query.count()
    total_revenue = db.session.query(db.func.sum(Sale.total_price)).scalar() or 0
    
    # Get last cashout date for each cashier
    cashiers = User.query.filter_by(role='cashier').all()
    current_period_sales = []
    current_period_revenue = 0
    
    for cashier in cashiers:
        # Get last cashout for this cashier
        last_cashout = Cashout.query.filter_by(cashier_id=cashier.id).order_by(Cashout.date.desc()).first()
        
        if last_cashout:
            # Get sales since last cashout
            since_last_cashout = Sale.query.filter(
                Sale.cashier_id == cashier.id,
                Sale.date_sold > last_cashout.date
            ).all()
        else:
            # If no cashout yet, get all sales
            since_last_cashout = Sale.query.filter_by(cashier_id=cashier.id).all()
        
        current_period_sales.extend(since_last_cashout)
    
    current_period_sales_count = len(current_period_sales)
    current_period_revenue = sum(sale.total_price for sale in current_period_sales)
    
    # Calculate current period profit
    current_period_profit = 0
    for sale in current_period_sales:
        product = Product.query.get(sale.product_id)
        if product:
            profit_margin = product.get_profit_margin() / 100
            current_period_profit += sale.total_price * profit_margin
    
    return render_template(
        'admin_dashboard.html',
        total_products=total_products,
        low_stock_products=low_stock_products,
        products=products,
        today=today,
        today_sales_count=today_sales_count,
        today_revenue=today_revenue,
        today_profit=today_profit,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        current_period_sales_count=current_period_sales_count,
        current_period_revenue=current_period_revenue,
        current_period_profit=current_period_profit
    )

@app.route('/admin/products')
@login_required
def manage_products():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('manage_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        purchase_price = float(request.form.get('purchase_price'))
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        low_stock_threshold = int(request.form.get('low_stock_threshold'))
        
        product = Product(
            name=name,
            description=description,
            category=category,
            purchase_price=purchase_price,
            price=price,
            stock=stock,
            low_stock_threshold=low_stock_threshold
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.purchase_price = float(request.form.get('purchase_price'))
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.low_stock_threshold = int(request.form.get('low_stock_threshold'))
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/cashier/dashboard')
@login_required
def cashier_dashboard():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    
    if search_query:
        products = Product.query.filter(
            Product.stock > 0,
            Product.name.ilike(f'%{search_query}%')
        ).all()
    else:
        products = Product.query.filter(Product.stock > 0).all()
    
    # Get today's date
    today = datetime.utcnow().date()
    
    # Get today's sales
    today_sales = Sale.query.filter(
        Sale.cashier_id == current_user.id,
        db.func.date(Sale.date_sold) == today
    ).order_by(Sale.date_sold.desc()).all()
    
    today_revenue = sum(sale.total_price for sale in today_sales)
    
    # Get all-time sales for this cashier
    all_sales = Sale.query.filter_by(cashier_id=current_user.id).all()
    total_sales_count = len(all_sales)
    total_revenue = sum(sale.total_price for sale in all_sales)
    
    # Get sales since last cashout
    last_cashout = Cashout.query.filter_by(cashier_id=current_user.id).order_by(Cashout.date.desc()).first()
    
    if last_cashout:
        # Get sales since last cashout
        current_period_sales = Sale.query.filter(
            Sale.cashier_id == current_user.id,
            Sale.date_sold > last_cashout.date
        ).all()
        last_cashout_date = last_cashout.date
    else:
        # If no cashout yet, all sales are in current period
        current_period_sales = all_sales
        last_cashout_date = None
    
    current_period_sales_count = len(current_period_sales)
    current_period_revenue = sum(sale.total_price for sale in current_period_sales)
    
    # Get uncashed sales amount (should be the same as current period)
    uncashed_sales = Sale.query.filter_by(
        cashier_id=current_user.id,
        is_cashed_out=False
    ).all()
    
    uncashed_amount = sum(sale.total_price for sale in uncashed_sales)
    
    return render_template(
        'cashier_dashboard.html',
        products=products,
        today=today,
        today_sales=today_sales,
        today_revenue=today_revenue,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        current_period_sales_count=current_period_sales_count,
        current_period_revenue=current_period_revenue,
        last_cashout_date=last_cashout_date,
        search_query=search_query,
        uncashed_amount=uncashed_amount
    )

@app.route('/cashier/sell', methods=['POST'])
@login_required
def sell_product():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('login'))
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.stock < quantity:
        flash(f'Not enough stock available. Only {product.stock} units left.', 'danger')
        return redirect(url_for('cashier_dashboard'))
    
    total_price = product.price * quantity
    
    sale = Sale(
        product_id=product_id,
        quantity=quantity,
        total_price=total_price,
        cashier_id=current_user.id
    )
    
    product.stock -= quantity
    
    db.session.add(sale)
    db.session.commit()
    
    flash('Sale recorded successfully!', 'success')
    return redirect(url_for('cashier_dashboard'))

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if Sale.query.filter_by(product_id=product_id).first():
        flash('Cannot delete product with sales records.', 'danger')
        return redirect(url_for('manage_products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/sales')
@login_required
def view_sales():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    # Get all sales
    sales = Sale.query.order_by(Sale.date_sold.desc()).all()
    
    # Calculate total revenue
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Calculate total profit (estimated based on product profit margins)
    total_profit = 0
    
    # Create category summary
    category_summary = {}
    categories = []
    
    for sale in sales:
        product = Product.query.get(sale.product_id)
        if product:
            # Calculate profit for this sale
            profit_margin = product.get_profit_margin() / 100
            sale_profit = sale.total_price * profit_margin
            total_profit += sale_profit
            
            # Add to category summary
            category = product.category or 'Uncategorized'
            if category not in categories:
                categories.append(category)
            
            if category not in category_summary:
                category_summary[category] = {'count': 0, 'revenue': 0, 'profit': 0}
            
            category_summary[category]['count'] += sale.quantity
            category_summary[category]['revenue'] += sale.total_price
            category_summary[category]['profit'] += sale_profit
    
    return render_template(
        'view_sales.html',
        sales=sales,
        total_revenue=total_revenue,
        total_profit=total_profit,
        category_summary=category_summary,
        categories=categories,
        start_date='',
        end_date='',
        selected_category='all'
    )

@app.route('/cashier/sales')
@login_required
def view_cashier_sales():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('login'))
    
    # Get all sales for this cashier
    sales = Sale.query.filter_by(cashier_id=current_user.id).order_by(Sale.date_sold.desc()).all()
    
    # Calculate total revenue
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Get today's sales
    today = datetime.utcnow().date()
    today_sales = [sale for sale in sales if sale.date_sold.date() == today]
    today_revenue = sum(sale.total_price for sale in today_sales)
    
    # Create category summary
    category_summary = {}
    categories = []
    
    for sale in sales:
        product = Product.query.get(sale.product_id)
        if product:
            category = product.category or 'Uncategorized'
            if category not in categories:
                categories.append(category)
            
            if category not in category_summary:
                category_summary[category] = {'count': 0, 'revenue': 0}
            
            category_summary[category]['count'] += sale.quantity
            category_summary[category]['revenue'] += sale.total_price
    
    return render_template(
        'cashier_sales.html',
        sales=sales,
        total_revenue=total_revenue,
        today_sales=today_sales,
        today_revenue=today_revenue,
        category_summary=category_summary,
        categories=categories,
        start_date='',
        end_date='',
        selected_category='all'
    )

@app.route('/admin/cashout', methods=['GET', 'POST'])
@login_required
def admin_cashout():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    cashiers = User.query.filter_by(role='cashier').all()
    
    if request.method == 'POST':
        cashier_id = request.form.get('cashier_id')
        note = request.form.get('note', '')
        
        cashier = User.query.get_or_404(cashier_id)
        
        # Get all uncashed sales for this cashier
        uncashed_sales = Sale.query.filter_by(
            cashier_id=cashier_id,
            is_cashed_out=False
        ).all()
        
        if not uncashed_sales:
            flash('No sales to cash out for this cashier.', 'warning')
            return redirect(url_for('admin_cashout'))
        
        # Calculate total amount
        total_amount = sum(sale.total_price for sale in uncashed_sales)
        
        # Create new cashout record
        cashout = Cashout(
            cashier_id=cashier_id,
            admin_id=current_user.id,
            amount=total_amount,
            note=note
        )
        db.session.add(cashout)
        db.session.flush()  # Get the cashout ID
        
        # Mark all sales as cashed out
        for sale in uncashed_sales:
            sale.is_cashed_out = True
            sale.cashout_id = cashout.id
        
        db.session.commit()
        
        flash(f'Successfully cashed out {cashier.username} for RWF {total_amount:.0f}', 'success')
        return redirect(url_for('admin_cashout'))
    
    # Get cashiers with pending sales
    cashiers_with_sales = []
    for cashier in cashiers:
        # Get uncashed sales for this cashier
        uncashed_sales = Sale.query.filter_by(
            cashier_id=cashier.id,
            is_cashed_out=False
        ).all()
        
        if uncashed_sales:
            total_amount = sum(sale.total_price for sale in uncashed_sales)
            cashiers_with_sales.append({
                'cashier': cashier,
                'total_amount': total_amount,
                'sales_count': len(uncashed_sales)
            })
    
    # Get recent cashouts
    recent_cashouts = Cashout.query.order_by(Cashout.date.desc()).limit(10).all()
    
    return render_template(
        'admin_cashout.html',
        cashiers_with_sales=cashiers_with_sales,
        recent_cashouts=recent_cashouts
    )

@app.route('/admin/cashout/history')
@login_required
def cashout_history():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    cashouts = Cashout.query.order_by(Cashout.date.desc()).all()
    
    # Calculate total amount cashed out
    total_cashed_out = sum(cashout.amount for cashout in cashouts)
    
    return render_template(
        'cashout_history.html',
        cashouts=cashouts,
        total_cashed_out=total_cashed_out
    )

@app.route('/admin/cashout/details/<int:cashout_id>')
@login_required
def cashout_details(cashout_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    
    cashout = Cashout.query.get_or_404(cashout_id)
    sales = Sale.query.filter_by(cashout_id=cashout_id).all()
    
    return render_template(
        'cashout_details.html',
        cashout=cashout,
        sales=sales
    )

@app.route('/cashier/sales_status')
@login_required
def cashier_sales_status():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('login'))
    
    # Get all uncashed sales for this cashier
    uncashed_sales = Sale.query.filter_by(
        cashier_id=current_user.id,
        is_cashed_out=False
    ).order_by(Sale.date_sold.desc()).all()
    
    # Calculate total uncashed amount
    total_uncashed = sum(sale.total_price for sale in uncashed_sales)
    
    # Get recent cashouts for this cashier
    recent_cashouts = Cashout.query.filter_by(
        cashier_id=current_user.id
    ).order_by(Cashout.date.desc()).limit(5).all()
    
    # Get last cashout date
    last_cashout = Cashout.query.filter_by(
        cashier_id=current_user.id
    ).order_by(Cashout.date.desc()).first()
    
    last_cashout_date = last_cashout.date if last_cashout else None
    
    # Enrich cashout objects with their associated sales
    for cashout in recent_cashouts:
        cashout_sales = Sale.query.filter_by(
            cashout_id=cashout.id
        ).all()
        cashout.sales = cashout_sales
    
    return render_template(
        'cashier_sales_status.html',
        uncashed_sales=uncashed_sales,
        total_uncashed=total_uncashed,
        recent_cashouts=recent_cashouts,
        last_cashout_date=last_cashout_date
    )

@app.route('/admin/delete_sale/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    if current_user.role != 'admin':
        flash(_('Access denied. Admin privileges required.'), 'danger')
        return redirect(url_for('login'))
    
    sale = Sale.query.get_or_404(sale_id)
    
    # Check if the sale is already cashed out
    if sale.is_cashed_out:
        flash(_('Cannot delete a sale that has been cashed out.'), 'danger')
        return redirect(url_for('view_sales'))
    
    # Restore stock to product
    product = sale.product
    product.stock += sale.quantity
    
    # Log the deletion
    logger.info(f"Admin {current_user.username} deleted sale ID {sale.id} for {sale.quantity} units of {product.name}")
    
    # Delete the sale
    db.session.delete(sale)
    db.session.commit()
    
    flash(_('Sale deleted successfully. Stock has been restored.'), 'success')
    return redirect(url_for('view_sales'))

def initialize_database():
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='renoir01').first()
    if not admin:
        admin = User(username='renoir01', role='admin')
        admin.set_password('Renoir@654')
        db.session.add(admin)
    
    # Check if cashier user exists
    cashier = User.query.filter_by(username='epi').first()
    if not cashier:
        cashier = User(username='epi', role='cashier')
        cashier.set_password('Epi@654')
        db.session.add(cashier)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_database()
    app.run(debug=True)
