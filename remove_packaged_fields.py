#!/usr/bin/env python
"""
Emergency Fix: Remove Packaged Products Fields
This script removes all references to packaged products from app.py
"""
import os
import sys
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("remove_packaged_fields.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("remove_packaged_fields")

def fix_app_py():
    """Remove all packaged product fields from app.py"""
    logger.info("Removing packaged product fields from app.py...")
    
    app_path = 'app.py'
    backup_path = f"{app_path}.remove_packaged_fields_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup
        if os.path.exists(app_path):
            shutil.copy2(app_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Read the current app.py
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the Product class definition
        product_class_start = content.find("class Product(db.Model):")
        if product_class_start == -1:
            logger.warning("Could not find Product class definition")
            return False
        
        # Find the next class definition or end of file
        next_class = content.find("class ", product_class_start + 1)
        if next_class == -1:
            next_class = len(content)
        
        # Extract the Product class
        product_class = content[product_class_start:next_class]
        
        # Remove packaged product fields
        product_class_lines = product_class.split('\n')
        filtered_lines = []
        for line in product_class_lines:
            if not any(field in line for field in ['is_packaged', 'units_per_package', 'individual_price', 'individual_stock']):
                filtered_lines.append(line)
        
        # Reconstruct the Product class
        updated_product_class = '\n'.join(filtered_lines)
        
        # Replace the Product class in the content
        updated_content = content[:product_class_start] + updated_product_class + content[next_class:]
        
        # Remove any other references to packaged products
        updated_content = updated_content.replace('if product.is_packaged:', '')
        updated_content = updated_content.replace('product.is_packaged =', '# product.is_packaged =')
        updated_content = updated_content.replace('product.units_per_package =', '# product.units_per_package =')
        updated_content = updated_content.replace('product.individual_price =', '# product.individual_price =')
        updated_content = updated_content.replace('product.individual_stock =', '# product.individual_stock =')
        
        # Fix any sell_product route logic that depends on packaged products
        sell_product_start = updated_content.find("@app.route('/cashier/sell'")
        if sell_product_start != -1:
            sell_product_end = updated_content.find("@app.route", sell_product_start + 1)
            if sell_product_end == -1:
                sell_product_end = len(updated_content)
            
            sell_product_code = updated_content[sell_product_start:sell_product_end]
            
            # Replace complex packaged product logic with simple logic
            if 'if product.is_packaged:' in sell_product_code:
                simple_logic = """
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
        """
                # Find where the complex logic starts
                complex_start = sell_product_code.find('# Calculate total price')
                if complex_start != -1:
                    complex_end = sell_product_code.find('db.session.add(sale)', complex_start)
                    if complex_end != -1:
                        # Replace the complex logic with simple logic
                        sell_product_code = sell_product_code[:complex_start] + simple_logic + sell_product_code[complex_end:]
                        # Update the full content
                        updated_content = updated_content[:sell_product_start] + sell_product_code + updated_content[sell_product_end:]
        
        # Write the updated content back to app.py
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Successfully removed packaged product fields from app.py")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing app.py: {e}")
        return False

def fix_templates():
    """Remove packaged product fields from templates"""
    logger.info("Removing packaged product fields from templates...")
    
    template_files = [
        'templates/add_product.html',
        'templates/edit_product.html',
        'templates/cashier_dashboard.html'
    ]
    
    for template_file in template_files:
        try:
            if not os.path.exists(template_file):
                logger.warning(f"Template file not found: {template_file}")
                continue
            
            backup_path = f"{template_file}.remove_packaged_fields_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(template_file, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove packaged product fields and related JavaScript
            content = content.replace('id="is_packaged"', 'id="is_packaged" style="display:none;"')
            content = content.replace('id="units_per_package"', 'id="units_per_package" style="display:none;"')
            content = content.replace('id="individual_price"', 'id="individual_price" style="display:none;"')
            content = content.replace('id="individual_stock"', 'id="individual_stock" style="display:none;"')
            
            # Remove any JavaScript that shows/hides packaged product fields
            if 'function togglePackagedFields()' in content:
                js_start = content.find('<script>')
                if js_start != -1:
                    js_end = content.find('</script>', js_start)
                    if js_end != -1:
                        js_content = content[js_start:js_end + 9]
                        # Remove the togglePackagedFields function
                        updated_js = js_content.replace('function togglePackagedFields() {', '/* function togglePackagedFields() {')
                        updated_js = updated_js.replace('togglePackagedFields();', '/* togglePackagedFields(); */')
                        updated_js = updated_js.replace('$("#is_packaged").change(togglePackagedFields);', '/* $("#is_packaged").change(togglePackagedFields); */')
                        content = content[:js_start] + updated_js + content[js_end + 9:]
            
            # Remove sale type selection in cashier dashboard
            if 'name="sale_type"' in content:
                sale_type_start = content.find('<div class="form-group">')
                if sale_type_start != -1:
                    sale_type_end = content.find('</div>', sale_type_start)
                    if sale_type_end != -1 and 'sale_type' in content[sale_type_start:sale_type_end]:
                        content = content[:sale_type_start] + content[sale_type_end + 6:]
            
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully updated template: {template_file}")
        
        except Exception as e:
            logger.error(f"Error fixing template {template_file}: {e}")
    
    return True

if __name__ == "__main__":
    print("Running emergency fix to remove packaged products fields...")
    
    success = fix_app_py()
    if success:
        print("Successfully removed packaged product fields from app.py")
    else:
        print("Failed to remove packaged product fields from app.py")
    
    success = fix_templates()
    if success:
        print("Successfully removed packaged product fields from templates")
    else:
        print("Failed to remove packaged product fields from templates")
    
    print("\nEmergency fix completed!")
    print("\nInstructions:")
    print("1. Reload your web app from the PythonAnywhere Web tab")
    print("2. Clear your browser cookies and cache")
    print("3. Try accessing the site again")
    print("\nThis fix completely removes the packaged products feature to restore basic functionality")
