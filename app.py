from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
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
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

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
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('cashier_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    low_stock_products = [p for p in products if p.is_low_stock()]
    
    # Get today's sales
    today = datetime.today().date()
    today_sales = Sale.query.filter(db.func.date(Sale.date_sold) == today).all()
    total_revenue = sum(sale.total_price for sale in today_sales)
    
    return render_template('admin_dashboard.html', 
                          products=products,
                          low_stock_products=low_stock_products,
                          today_sales=today_sales,
                          total_revenue=total_revenue)

@app.route('/admin/products')
@login_required
def manage_products():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('manage_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        low_stock_threshold = int(request.form.get('low_stock_threshold'))
        
        product = Product(
            name=name,
            description=description,
            category=category,
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
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.low_stock_threshold = int(request.form.get('low_stock_threshold'))
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Check if the product has associated sales
    if product.sales and len(product.sales) > 0:
        flash(f'Cannot delete product "{product.name}" because it has associated sales records. Consider updating the product instead.', 'danger')
        return redirect(url_for('manage_products'))
    
    # If no sales are associated, proceed with deletion
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/sales')
@login_required
def view_sales():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    cashier_id = request.args.get('cashier_id')
    category = request.args.get('category')
    
    # Base query
    query = Sale.query
    
    # Apply filters
    if date_from:
        query = query.filter(Sale.date_sold >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Sale.date_sold <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if cashier_id:
        query = query.filter(Sale.cashier_id == int(cashier_id))
    if category:
        query = query.join(Product).filter(Product.category == category)
    
    # Get results
    sales = query.order_by(Sale.date_sold.desc()).all()
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Get all cashiers for the filter dropdown
    cashiers = User.query.filter_by(role='cashier').all()
    
    # Get all categories for the filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    
    # Group sales by category for the summary
    sales_by_category = {}
    for sale in sales:
        category = sale.product.category
        if category not in sales_by_category:
            sales_by_category[category] = {
                'quantity': 0,
                'revenue': 0,
                'sales': []
            }
        
        sales_by_category[category]['quantity'] += sale.quantity
        sales_by_category[category]['revenue'] += sale.total_price
        sales_by_category[category]['sales'].append(sale)
    
    return render_template('view_sales.html', 
                          sales=sales,
                          total_revenue=total_revenue,
                          cashiers=cashiers,
                          date_from=date_from,
                          date_to=date_to,
                          selected_cashier_id=cashier_id,
                          categories=categories,
                          selected_category=category,
                          sales_by_category=sales_by_category)

@app.route('/cashier/dashboard')
@login_required
def cashier_dashboard():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.filter(Product.stock > 0).all()
    
    # Get today's sales for this cashier
    today = datetime.today().date()
    today_sales = Sale.query.filter(
        db.func.date(Sale.date_sold) == today,
        Sale.cashier_id == current_user.id
    ).all()
    total_revenue = sum(sale.total_price for sale in today_sales)
    
    return render_template('cashier_dashboard.html', 
                          products=products,
                          today_sales=today_sales,
                          total_revenue=total_revenue)

@app.route('/cashier/sell', methods=['POST'])
@login_required
def sell_product():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('index'))
    
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))
    
    product = Product.query.get_or_404(product_id)
    
    if product.stock < quantity:
        flash(f'Not enough stock available. Only {product.stock} units left.', 'danger')
        return redirect(url_for('cashier_dashboard'))
    
    # Calculate total price
    total_price = product.price * quantity
    
    # Create sale record
    sale = Sale(
        product_id=product_id,
        quantity=quantity,
        total_price=total_price,
        cashier_id=current_user.id
    )
    
    # Update product stock
    product.stock -= quantity
    
    db.session.add(sale)
    db.session.commit()
    
    flash('Sale recorded successfully!', 'success')
    return redirect(url_for('cashier_dashboard'))

@app.route('/cashier/sales')
@login_required
def view_cashier_sales():
    if current_user.role != 'cashier':
        flash('Access denied. Cashier privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    category = request.args.get('category')
    
    # Base query - only show this cashier's sales
    query = Sale.query.filter(Sale.cashier_id == current_user.id)
    
    # Apply filters
    if date_from:
        query = query.filter(Sale.date_sold >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Sale.date_sold <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if category:
        query = query.join(Product).filter(Product.category == category)
    
    # Get results
    sales = query.order_by(Sale.date_sold.desc()).all()
    total_revenue = sum(sale.total_price for sale in sales)
    
    # Get all categories for the filter dropdown
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    
    # Group sales by category for the summary
    sales_by_category = {}
    for sale in sales:
        category = sale.product.category
        if category not in sales_by_category:
            sales_by_category[category] = {
                'quantity': 0,
                'revenue': 0,
                'sales': []
            }
        
        sales_by_category[category]['quantity'] += sale.quantity
        sales_by_category[category]['revenue'] += sale.total_price
        sales_by_category[category]['sales'].append(sale)
    
    return render_template('cashier_sales.html', 
                          sales=sales,
                          total_revenue=total_revenue,
                          date_from=date_from,
                          date_to=date_to,
                          categories=categories,
                          selected_category=category,
                          sales_by_category=sales_by_category)

# Initialize the database and create an admin user
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # Check if admin user already exists
    admin = User.query.filter_by(username='renoir01').first()
    if not admin:
        admin = User(username='renoir01', role='admin')
        admin.set_password('Renoir@654')
        db.session.add(admin)
    
    # Check if cashier user already exists
    cashier = User.query.filter_by(username='cashier').first()
    if not cashier:
        cashier = User(username='cashier', role='cashier')
        cashier.set_password('cashier123')
        db.session.add(cashier)
    
    db.session.commit()
    print('Database initialized with admin and cashier users.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='renoir01').first()
        if not admin:
            admin = User(username='renoir01', role='admin')
            admin.set_password('Renoir@654')
            db.session.add(admin)
        
        # Check if cashier user already exists
        cashier = User.query.filter_by(username='cashier').first()
        if not cashier:
            cashier = User(username='cashier', role='cashier')
            cashier.set_password('cashier123')
            db.session.add(cashier)
        
        db.session.commit()
    
    app.run(debug=True)
