import os
import sys
import logging
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("init_db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if running on PythonAnywhere
is_pythonanywhere = os.environ.get('PYTHONANYWHERE_SITE') is not None

# Get username for PythonAnywhere paths
username = os.environ.get('USER', 'renoir0')

# Set up proper paths for PythonAnywhere if needed
if is_pythonanywhere:
    logger.info("Running on PythonAnywhere, setting up environment")
    project_path = f'/home/{username}/SmartInventory'
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
    os.environ['PYTHONANYWHERE_SITE'] = 'true'
    logger.info(f"Added {project_path} to Python path")

# Now import app components after path setup
from app import app, db, User, Product

def init_db():
    """Initialize the database with tables and default admin user."""
    logger.info("Creating database tables...")
    with app.app_context():
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            logger.info("Creating default admin user...")
            admin = User(
                username='renoir01',
                password_hash=generate_password_hash('Renoir@654'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created.")
        else:
            logger.info("Admin user already exists.")
        
        # Check if other required tables exist by querying them
        try:
            product_count = Product.query.count()
            logger.info(f"Product table exists with {product_count} products")
        except Exception as e:
            logger.error(f"Error checking Product table: {str(e)}")
        
        logger.info("Database initialization complete.")

if __name__ == "__main__":
    logger.info("Starting database initialization")
    try:
        init_db()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise
