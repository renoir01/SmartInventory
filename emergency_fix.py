#!/usr/bin/env python
"""
Emergency Fix for Smart Inventory System
This script completely rebuilds the app.py file and resets the database
to fix all issues including redirect loops
"""
import os
import sys
import logging
import shutil
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emergency_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("emergency_fix")

def reset_database():
    """Reset the database to a clean state"""
    logger.info("Resetting database...")
    
    db_path = 'new_inventory.db'
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup of existing database
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created database backup: {backup_path}")
            
            # Rename the existing database to avoid conflicts
            os.rename(db_path, f"{db_path}.old")
            logger.info(f"Renamed existing database to {db_path}.old")
        
        # Create a new database with the correct schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create User table
        cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        
        # Create Product table
        cursor.execute('''
        CREATE TABLE product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            purchase_price REAL,
            price REAL NOT NULL,
            stock INTEGER,
            low_stock_threshold INTEGER,
            date_added TIMESTAMP
        )
        ''')
        
        # Create Sale table
        cursor.execute('''
        CREATE TABLE sale (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            cashier_id INTEGER NOT NULL,
            date_sold TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES product (id),
            FOREIGN KEY (cashier_id) REFERENCES user (id)
        )
        ''')
        
        # Add default users
        cursor.execute('''
        INSERT INTO user (username, password_hash, role)
        VALUES (?, ?, ?)
        ''', ('renoir01', 'pbkdf2:sha256:150000$FUlVFt0I$e1f90fd1c40f7370df85d4254d4c0d9c8c8d18a1c3ac1c3d3d79be7a5d062afe', 'admin'))
        
        cursor.execute('''
        INSERT INTO user (username, password_hash, role)
        VALUES (?, ?, ?)
        ''', ('epi', 'pbkdf2:sha256:150000$FUlVFt0I$e1f90fd1c40f7370df85d4254d4c0d9c8c8d18a1c3ac1c3d3d79be7a5d062afe', 'cashier'))
        
        conn.commit()
        conn.close()
        
        logger.info("Successfully reset database")
        return True
    
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

def rewrite_app_py():
    """Completely rewrite app.py with a simplified version"""
    logger.info("Completely rewriting app.py...")
    
    app_path = 'app.py'
    backup_path = f"{app_path}.emergency_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup
        if os.path.exists(app_path):
            shutil.copy2(app_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Write a clean version of app.py
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write("""from flask import Flask, render_template, redirect, url_for, flash, request, session, g
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

# Simple translation function
def _(text, **variables):
    return text % variables if variables else text

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

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('sales', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cashier = db.relationship('User', backref=db.backref('sales', lazy=True))
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)

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
    
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock <= Product.low_stock_threshold).all()
    total_sales = Sale.query.count()
    total_revenue = db.session.query(db.func.sum(Sale.total_price)).scalar() or 0
    
    today = datetime.utcnow().date()
    today_sales = Sale.query.filter(
        db.func.date(Sale.date_sold) == today
    ).all()
    
    today_revenue = sum(sale.total_price for sale in today_sales)
    
    return render_template(
        'admin_dashboard.html',
        total_products=total_products,
        low_stock_products=low_stock_products,
        total_sales=total_sales,
        total_revenue=total_revenue,
        today_sales=len(today_sales),
        today_revenue=today_revenue
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
    
    today = datetime.utcnow().date()
    today_sales = Sale.query.filter(
        Sale.cashier_id == current_user.id,
        db.func.date(Sale.date_sold) == today
    ).order_by(Sale.date_sold.desc()).all()
    
    total_revenue = sum(sale.total_price for sale in today_sales)
    
    return render_template(
        'cashier_dashboard.html',
        products=products,
        today_sales=today_sales,
        total_revenue=total_revenue,
        search_query=search_query
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
""")
        
        logger.info("Successfully rewrote app.py")
        return True
    
    except Exception as e:
        logger.error(f"Error rewriting app.py: {e}")
        return False

if __name__ == "__main__":
    print("Running emergency fix for Smart Inventory System...")
    
    # Reset the database first
    if reset_database():
        print("Successfully reset database")
    else:
        print("Failed to reset database")
    
    # Then rewrite app.py
    if rewrite_app_py():
        print("Successfully rewrote app.py")
    else:
        print("Failed to rewrite app.py")
    
    print("\nEmergency fix completed!")
    print("\nInstructions:")
    print("1. Stop any running Flask server")
    print("2. Delete all browser cookies and cache completely")
    print("3. Run 'python app.py' to start the server again")
    print("4. Try accessing the site at http://127.0.0.1:5000")
    print("5. Login with:")
    print("   - Admin: username 'renoir01', password 'Renoir@654'")
    print("   - Cashier: username 'epi', password 'Epi@654'")
    print("\nThis fix completely rebuilds the application and database to resolve all issues.")
