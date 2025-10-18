# app.py
from flask import Flask, jsonify, render_template, request
import csv
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# --- Helper Functions ---

def get_medicine_status(medicine):
    """Determines the status of a medicine based on quantity and expiry date."""
    try:
        expiry_date = datetime.strptime(medicine['expiry_date'], '%Y-%m-%d')
        quantity = int(medicine.get('quantity', 0))
        today = datetime.now()
        thirty_days_from_now = today + timedelta(days=30)

        if quantity <= 0:
            return {'text': 'Out of Stock', 'className': 'status-out-of-stock'}
        if today <= expiry_date <= thirty_days_from_now:
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

# --- Main Page Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inventory')
def inventory_page():
    inventory = load_data_from_csv('inventory.csv')
    for item in inventory:
        item['status'] = get_medicine_status(item)
    return render_template('inventory.html', inventory=inventory)

@app.route('/low_stock')
def low_stock_page():
    inventory = load_data_from_csv('inventory.csv')
    low_stock_items = [item for item in inventory if item.get('quantity') and 0 < int(item.get('quantity', 0)) <= 20]
    for item in low_stock_items:
        item['status'] = get_medicine_status(item)
    return render_template('low_stock.html', low_stock_items=low_stock_items)

@app.route('/billing')
def billing_page():
    return render_template('billing.html')

@app.route('/sales')
def sales_page():
    return render_template('sales.html')

@app.route('/previous_sales')
def previous_sales_page():
    return render_template('sales.html')



@app.route('/api/inventory/search')
def search_inventory():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    inventory = load_data_from_csv('inventory.csv')
    
    filtered_inventory = [
        item for item in inventory if
        (query in item.get('name', '').lower() or query in item.get('Manufacturer', '').lower())
    ]
    
    for item in filtered_inventory:
        item['status'] = get_medicine_status(item)
        
    return jsonify(filtered_inventory)

@app.route('/api/inventory/add', methods=['POST'])
def add_medicine():
    data = request.get_json()
    inventory = load_data_from_csv('inventory.csv')
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

    save_data_to_csv('inventory.csv', inventory, fieldnames)
    return jsonify({"success": True, "message": message})


@app.route('/api/billing/create', methods=['POST'])
def create_bill():
    sale_data = request.get_json()
    items_sold = sale_data.get('items', [])
    
    if not items_sold:
        return jsonify({"success": False, "message": "No items in bill."}), 400

    inventory = load_data_from_csv('inventory.csv')
    inventory_dict = {item['id']: item for item in inventory}

    for item in items_sold:
        item_id = str(item.get('id'))
        quantity_sold = int(item.get('quantity', 0))
        if item_id not in inventory_dict or int(inventory_dict[item_id]['quantity']) < quantity_sold:
            return jsonify({"success": False, "message": f"Not enough stock for {item.get('name')}."}), 400

    for item in items_sold:
        item_id = str(item.get('id'))
        inventory_dict[item_id]['quantity'] = str(int(inventory_dict[item_id]['quantity']) - int(item['quantity']))
    
    inventory_fieldnames = ['id', 'name', 'Manufacturer', 'expiry_date', 'quantity', 'price']
    save_data_to_csv('inventory.csv', list(inventory_dict.values()), inventory_fieldnames)

    sales = load_data_from_csv('sales.csv')
    try:
        new_bill_id = max([int(b['bill_id']) for b in sales if b.get('bill_id', '').isdigit()]) + 1 if sales else 1
    except (ValueError, IndexError):
        new_bill_id = 1

    now = datetime.now()

    for item in items_sold:
        new_sale_record = {
            'bill_id': new_bill_id,
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'product_id': item['id'],
            'product_name': item['name'],
            'quantity': item['quantity'],
            'unit_price': item['price'],
            'total_amount': float(item.get('price', 0)) * int(item.get('quantity', 0))
        }
        sales.append(new_sale_record)

    sales_fieldnames = ['bill_id', 'date', 'time', 'product_id', 'product_name', 'quantity', 'unit_price', 'total_amount']
    save_data_to_csv('sales.csv', sales, sales_fieldnames)
    
    return jsonify({
        "success": True, 
        "message": "Sale processed successfully.",
        "bill_id": new_bill_id
    })


@app.route('/api/inventory/summary')
def inventory_summary():
    inventory = load_data_from_csv('inventory.csv')
    total_quantity = sum(int(item.get('quantity', 0)) for item in inventory)
    return jsonify({"total_quantity": total_quantity})

@app.route('/api/inventory/low_stock')
def low_stock_summary():
    inventory = load_data_from_csv('inventory.csv')
    low_stock_count = sum(1 for item in inventory if item.get('quantity') and 0 < int(item.get('quantity', 0)) <= 20)
    return jsonify({"low_stock_count": low_stock_count})

@app.route('/api/sales/summary')
def sales_summary():
    sales = load_data_from_csv('sales.csv')
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_sales = sum(float(s.get('total_amount', 0)) for s in sales if s.get('date') == today_str)
    return jsonify({"todays_sales": todays_sales})

@app.route('/api/sales/today')
def get_todays_sales():
    sales = load_data_from_csv('sales.csv')
    today_str = datetime.now().strftime('%Y-%m-%d')
    return jsonify([s for s in sales if s.get('date') == today_str])

@app.route('/api/sales/previous/all')
def get_previous_sales():
    sales = load_data_from_csv('sales.csv')
    today_str = datetime.now().strftime('%Y-%m-%d')
    return jsonify([s for s in sales if s.get('date') != today_str])

@app.route('/api/sales/kpi_summary/today')
def sales_kpi_summary_today():
    sales = load_data_from_csv('sales.csv')
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_sales = [s for s in sales if s.get('date') == today_str]
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in todays_sales),
        "total_transactions": len(set(s.get('bill_id') for s in todays_sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in todays_sales)
    })

@app.route('/api/sales/kpi_summary/previous')
def sales_kpi_summary_previous():
    sales = load_data_from_csv('sales.csv')
    today_str = datetime.now().strftime('%Y-%m-%d')
    previous_sales = [s for s in sales if s.get('date') != today_str]
    return jsonify({
        "total_revenue": sum(float(s.get('total_amount', 0)) for s in previous_sales),
        "total_transactions": len(set(s.get('bill_id') for s in previous_sales)),
        "total_items_sold": sum(int(s.get('quantity', 0)) for s in previous_sales)
    })

@app.route('/api/inventory/expiring_soon')
def expiring_soon():
    inventory = load_data_from_csv('inventory.csv')
    today = datetime.now()
    thirty_days_from_now = today + timedelta(days=30)
    expiring_soon_items = []
    for item in inventory:
        try:
            expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
            if today <= expiry_date <= thirty_days_from_now:
                item['status'] = get_medicine_status(item)
                expiring_soon_items.append(item)
        except (ValueError, KeyError):
            continue
    return jsonify(expiring_soon_items)

@app.route('/api/inventory/status_distribution')
def get_status_distribution():
    inventory = load_data_from_csv('inventory.csv')
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
def get_all_inventory():
    inventory = load_data_from_csv('inventory.csv')
    for item in inventory:
        item['status'] = get_medicine_status(item)
    return jsonify(inventory)

if __name__ == '__main__':
    app.run(debug=True)