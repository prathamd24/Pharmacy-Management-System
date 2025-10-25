# app.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from datetime import datetime, timedelta
import os

app = Flask(__name__)
# You MUST set a secret key for sessions to work
app.config['SECRET_KEY'] = 'your_secret_key_here' 

# --- Authentication & User Management ---

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# If a user tries to access a protected page, redirect them to the login page
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        """Load user by ID"""
        users = load_data_from_csv('users.csv')
        for user in users:
            if user.get('id') == user_id:
                return User(user['id'], user['username'], user['password_hash'])
        return None

    @staticmethod
    def get_by_username(username):
        """Load user by username"""
        users = load_data_from_csv('users.csv')
        for user in users:
            if user.get('username').lower() == username.lower():
                return User(user['id'], user['username'], user['password_hash'])
        return None

@login_manager.user_loader
def load_user(user_id):
    """Required callback for Flask-Login to load a user from session"""
    return User.get(user_id)

# --- Authentication Routes (NEW) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check username and password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.get_by_username(username):
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        users = load_data_from_csv('users.csv')
        user_fieldnames = ['id', 'username', 'password_hash']
        
        try:
            new_id = max([int(u['id']) for u in users if u.get('id', '').isdigit()]) + 1 if users else 1
        except (ValueError, IndexError):
            new_id = 1
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256:1000000')
        
        new_user = {
            'id': new_id,
            'username': username,
            'password_hash': hashed_password
        }
        users.append(new_user)
        save_data_to_csv('users.csv', users, user_fieldnames)

        # --- Create user-specific files ---
        # This is the core of your request
        inventory_fieldnames = ['id', 'name', 'Manufacturer', 'expiry_date', 'quantity', 'price']
        sales_fieldnames = ['bill_id', 'date', 'time', 'product_id', 'product_name', 'quantity', 'unit_price', 'total_amount']
        
        # Create empty inventory file
        save_data_to_csv(f"{username}_inventory.csv", [], inventory_fieldnames)
        # Create empty sales file
        save_data_to_csv(f"{username}_sales.csv", [], sales_fieldnames)
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# --- Helper Functions (MODIFIED) ---

def get_user_inventory_file():
    """Gets the inventory file path for the currently logged-in user."""
    return f"{current_user.username}_inventory.csv"

def get_user_sales_file():
    """Gets the sales file path for the currently logged-in user."""
    return f"{current_user.username}_sales.csv"

@app.context_processor
def inject_user():
    """Injects the 'current_user' variable into all templates."""
    return dict(current_user=current_user)

def get_medicine_status(medicine):
    """Determines the status of a medicine based on quantity and expiry date."""
    try:
        expiry_date = datetime.strptime(medicine['expiry_date'], '%Y-%m-%d')
        quantity = int(medicine.get('quantity', 0))
        today = datetime.now()
        ninety_days_from_now = today + timedelta(days=90) 

        if quantity <= 0:
            return {'text': 'Out of Stock', 'className': 'status-out-of-stock'}
        if today <= expiry_date <= ninety_days_from_now: 
            return {'text': 'Expiring Soon', 'className': 'status-expiring-soon'}
        if quantity <= 20:
            return {'text': 'Low Stock', 'className': 'status-low-stock'}
        return {'text': 'In Stock', 'className': 'status-in-stock'}
    except (ValueError, KeyError):
        return {'text': 'Unknown', 'className': ''}

def load_data_from_csv(filename):
    """Generic function to load data from a given CSV file."""
    data = []
    if not os.path.exists(filename):
        return data
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return data

def save_data_to_csv(filename, data, fieldnames):
    """Generic function to save data to a given CSV file."""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        print(f"Error writing to {filename}: {e}")

# --- Main Page Routes (MODIFIED & PROTECTED) ---

@app.route('/')
@login_required  # Protect this route
def home():
    # Pass username to template (though context_processor does this automatically)
    return render_template('index.html', username=current_user.username)

@app.route('/inventory')
@login_required  # Protect this route
def inventory_page():
    # Load user-specific inventory
    inventory = load_data_from_csv(get_user_inventory_file())
    for item in inventory:
        item['status'] = get_medicine_status(item)
    return render_template('inventory.html', inventory=inventory, username=current_user.username)

@app.route('/low_stock')
@login_required  # Protect this route
def low_stock_page():
    # Load user-specific inventory
    inventory = load_data_from_csv(get_user_inventory_file())
    low_stock_items = [item for item in inventory if item.get('quantity') and 0 < int(item.get('quantity', 0)) <= 20]
    for item in low_stock_items:
        item['status'] = get_medicine_status(item)
    return render_template('low_stock.html', low_stock_items=low_stock_items, username=current_user.username)

@app.route('/billing')
@login_required  # Protect this route
def billing_page():
    return render_template('billing.html', username=current_user.username)

@app.route('/sales')
@login_required  # Protect this route
def sales_page():
    return render_template('sales.html', username=current_user.username)

@app.route('/account')
@login_required # Protect this route
def account_page():
    # This renders your new account.html page
    return render_template('account.html', username=current_user.username)


# --- API Routes (MODIFIED & PROTECTED) ---
# ALL API routes must be protected and use the helper functions

@app.route('/api/inventory/search')
@login_required
def search_inventory():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    # Load user-specific inventory
    inventory = load_data_from_csv(get_user_inventory_file())
    
    filtered_inventory = [
        item for item in inventory if
        (query in item.get('name', '').lower() or query in item.get('Manufacturer', '').lower())
    ]
    
    for item in filtered_inventory:
        item['status'] = get_medicine_status(item)
        
    return jsonify(filtered_inventory)

@app.route('/api/inventory/add', methods=['POST'])
@login_required
def add_medicine():
    data = request.get_json()
    # Load user-specific inventory
    user_inventory_file = get_user_inventory_file()
    inventory = load_data_from_csv(user_inventory_file)
    fieldnames = ['id', 'name', 'Manufacturer', 'expiry_date', 'quantity', 'price']
    
    medicine_name = data.get('name', '').strip()
    medicine_manufacturer = data.get('Manufacturer', '').strip()
    
    medicine_found = False
    message = ""
    for item in inventory:
        if item.get('name', '').strip().lower() == medicine_name.lower() and \
           item.get('Manufacturer', '').strip().lower() == medicine_manufacturer.lower():
            try:
                item['quantity'] = str(int(item.get('quantity', 0)) + int(data.get('quantity', 0)))
                if data.get('price'):
                    item['price'] = data.get('price')
                medicine_found = True
                message = "Medicine quantity updated."
                break
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Invalid quantity or price."}), 400

    if not medicine_found:
        try:
            new_id = max([int(item['id']) for item in inventory if item.get('id', '').isdigit()]) + 1 if inventory else 1
        except (ValueError, IndexError):
            new_id = 1
        
        new_medicine_data = {
            'id': new_id,
            'name': medicine_name,
            'Manufacturer': data.get('Manufacturer'),
            'expiry_date': data.get('expiry_date'),
            'quantity': data.get('quantity'),
            'price': data.get('price')
        }
        inventory.append(new_medicine_data)
        message = "New medicine added."

    # Save to user-specific inventory
    save_data_to_csv(user_inventory_file, inventory, fieldnames)
    return jsonify({"success": True, "message": message})


@app.route('/api/billing/create', methods=['POST'])
@login_required
def create_bill():
    sale_data = request.get_json()
    items_sold = sale_data.get('items', [])
    
    if not items_sold:
        return jsonify({"success": False, "message": "No items in bill."}), 400

    # Load user-specific files
    user_inventory_file = get_user_inventory_file()
    user_sales_file = get_user_sales_file()
    
    inventory = load_data_from_csv(user_inventory_file)
    sales = load_data_from_csv(user_sales_file)
    
    inventory_fieldnames = ['id', 'name', 'Manufacturer', 'expiry_date', 'quantity', 'price']
    sales_fieldnames = ['bill_id', 'date', 'time', 'product_id', 'product_name', 'quantity', 'unit_price', 'total_amount']

    try:
        if not sales:
            new_bill_id = 1
        else:
            new_bill_id = max(int(s.get('bill_id', 0)) for s in sales if s.get('bill_id', '0').isdigit()) + 1

        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M:%S')

        new_sales_entries = []
        
        for item_sold in items_sold:
            item_id = str(item_sold.get('id'))
            quantity_sold = int(item_sold.get('quantity', 0))

            if quantity_sold <= 0:
                 return jsonify({"success": False, "message": f"Invalid quantity for item ID {item_id}."}), 400

            item_found_in_inventory = False
            
            for inv_item in inventory:
                if inv_item.get('id') == item_id:
                    current_quantity = int(inv_item.get('quantity', 0))
                    
                    if current_quantity < quantity_sold:
                        return jsonify({"success": False, "message": f"Not enough stock for {inv_item.get('name')}."}), 400
                    
                    inv_item['quantity'] = str(current_quantity - quantity_sold)
                    item_found_in_inventory = True
                    
                    new_sales_entries.append({
                        'bill_id': new_bill_id,
                        'date': current_date,
                        'time': current_time,
                        'product_id': item_id,
                        'product_name': inv_item.get('name'),
                        'quantity': quantity_sold,
                        'unit_price': inv_item.get('price'),
                        'total_amount': round(float(inv_item.get('price', 0)) * quantity_sold, 2)
                    })
                    break
            
            if not item_found_in_inventory:
                return jsonify({"success": False, "message": f"Item with ID {item_id} not found in inventory."}), 404

        # Save to user-specific files
        save_data_to_csv(user_inventory_file, inventory, inventory_fieldnames)
        
        all_sales = sales + new_sales_entries
        save_data_to_csv(user_sales_file, all_sales, sales_fieldnames)

        return jsonify({
            "success": True, 
            "message": "Sale processed successfully.",
            "bill_id": new_bill_id
        })
    
    except Exception as e:
        print(f"Error in create_bill: {e}")
        return jsonify({"success": False, "message": f"An server error occurred: {e}"}), 500

# --- All other API routes refactored ---

@app.route('/api/inventory/summary')
@login_required
def inventory_summary():
    inventory = load_data_from_csv(get_user_inventory_file())
    total_quantity = sum(int(item.get('quantity', 0)) for item in inventory)
    return jsonify({"total_quantity": total_quantity})

@app.route('/api/inventory/low_stock')
@login_required
def low_stock_summary():
    inventory = load_data_from_csv(get_user_inventory_file())
    low_stock_count = sum(1 for item in inventory if item.get('quantity') and 0 < int(item.get('quantity', 0)) <= 20)
    return jsonify({"low_stock_count": low_stock_count})

@app.route('/api/sales/summary')
@login_required
def sales_summary():
    sales = load_data_from_csv(get_user_sales_file())
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_sales = sum(float(s.get('total_amount', 0)) for s in sales if s.get('date') == today_str)
    return jsonify({"todays_sales": todays_sales})

@app.route('/api/sales/today')
@login_required
def get_todays_sales():
    sales = load_data_from_csv(get_user_sales_file())
    today_str = datetime.now().strftime('%Y-%m-%d')
    return jsonify([s for s in sales if s.get('date') == today_str])

@app.route('/api/sales/previous/all')
@login_required
def get_previous_sales():
    sales = load_data_from_csv(get_user_sales_file())
    today_str = datetime.now().strftime('%Y-%m-%d')
    return jsonify([s for s in sales if s.get('date') != today_str])

@app.route('/api/sales/kpi_summary/today')
@login_required
def sales_kpi_summary_today():
    sales = load_data_from_csv(get_user_sales_file())
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_sales = [s for s in sales if s.get('date') == today_str]
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in todays_sales),
        "total_transactions": len(set(s.get('bill_id') for s in todays_sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in todays_sales)
    })

@app.route('/api/sales/kpi_summary/previous')
@login_required
def sales_kpi_summary_previous():
    sales = load_data_from_csv(get_user_sales_file())
    today_str = datetime.now().strftime('%Y-%m-%d')
    previous_sales = [s for s in sales if s.get('date') != today_str]
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in previous_sales),
        "total_transactions": len(set(s.get('bill_id') for s in previous_sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in previous_sales)
    })

@app.route('/api/inventory/expiring_soon')
@login_required
def expiring_soon():
    inventory = load_data_from_csv(get_user_inventory_file())
    today = datetime.now()
    ninety_days_from_now = today + timedelta(days=90) 
    expiring_soon_items = []
    for item in inventory:
        try:
            expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
            if today <= expiry_date <= ninety_days_from_now: 
                item['status'] = get_medicine_status(item)
                expiring_soon_items.append(item)
        except (ValueError, KeyError):
            continue
    return jsonify(expiring_soon_items)

@app.route('/api/inventory/status_distribution')
@login_required
def get_status_distribution():
    inventory = load_data_from_csv(get_user_inventory_file())
    if not inventory: return jsonify({})
    status_counts = {'In Stock': 0, 'Low Stock': 0, 'Out of Stock': 0, 'Expiring Soon': 0}
    for item in inventory:
        status_text = get_medicine_status(item)['text']
        if status_text in status_counts:
            status_counts[status_text] += 1
    total = len(inventory)
    return jsonify({
        "in_stock_percent": round((status_counts['In Stock'] / total) * 100) if total > 0 else 0,
        "low_stock_percent": round((status_counts['Low Stock'] / total) * 100) if total > 0 else 0,
        "out_of_stock_percent": round((status_counts['Out of Stock'] / total) * 100) if total > 0 else 0,
        "expiring_soon_percent": round((status_counts['Expiring Soon'] / total) * 100) if total > 0 else 0
    })

@app.route('/api/inventory/all')
@login_required
def get_all_inventory():
    inventory = load_data_from_csv(get_user_inventory_file())
    for item in inventory:
        item['status'] = get_medicine_status(item)
    return jsonify(inventory)

@app.route('/api/sales/all')
@login_required
def get_all_sales():
    sales = load_data_from_csv(get_user_sales_file())
    return jsonify(sales)

@app.route('/api/sales/kpi_summary/all')
@login_required
def sales_kpi_summary_all():
    sales = load_data_from_csv(get_user_sales_file())
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in sales),
        "total_transactions": len(set(s.get('bill_id') for s in sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in sales)
    })

@app.route('/api/sales/monthly')
@login_required
def get_monthly_sales():
    sales = load_data_from_csv(get_user_sales_file())
    today = datetime.now()
    current_month_str = today.strftime('%Y-%m-')
    
    monthly_sales = [
        s for s in sales 
        if s.get('date') and s['date'].startswith(current_month_str)
    ]
    return jsonify(monthly_sales)

@app.route('/api/sales/kpi_summary/monthly')
@login_required
def sales_kpi_summary_monthly():
    sales = load_data_from_csv(get_user_sales_file())
    today = datetime.now()
    current_month_str = today.strftime('%Y-%m-')
    
    monthly_sales = [
        s for s in sales 
        if s.get('date') and s['date'].startswith(current_month_str)
    ]
    
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in monthly_sales),
        "total_transactions": len(set(s.get('bill_id') for s in monthly_sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in monthly_sales)
    })

if __name__ == '__main__':
    app.run(debug=True)