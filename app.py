# app.py  --  Pharmacy Management System (upgraded)
import os
import csv
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, redirect,
    url_for, request, flash, session, jsonify
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------------ #
#  APP CONFIG
# ------------------------------------------------------------------ #
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

# ------------------------------------------------------------------ #
#  LOGIN MANAGER
# ------------------------------------------------------------------ #
login_manager = LoginManager(app)
login_manager.login_view = "login"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
USERS_FILE     = os.path.join(BASE_DIR, "users.csv")
DEMO_INVENTORY = os.path.join(BASE_DIR, "Demo_inventory.csv")
DEMO_SALES     = os.path.join(BASE_DIR, "Demo_sales.csv")

LOW_STOCK_THRESHOLD = 20
EXPIRY_SOON_DAYS    = 90


# ------------------------------------------------------------------ #
#  CSV HELPERS
# ------------------------------------------------------------------ #
def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(filepath, data, fields):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


# ------------------------------------------------------------------ #
#  USER-SPECIFIC FILE PATHS
# ------------------------------------------------------------------ #
def _username():
    if session.get("is_demo"):
        return "demo"
    return current_user.username


def inventory_file():
    return os.path.join(BASE_DIR, f"{_username()}_inventory.csv")


def sales_file():
    return os.path.join(BASE_DIR, f"{_username()}_sales.csv")


# ------------------------------------------------------------------ #
#  INVENTORY STATUS HELPER
# ------------------------------------------------------------------ #
def get_item_status(item):
    try:
        qty = int(item.get("quantity", 0))
    except (ValueError, TypeError):
        qty = 0

    expiry_str = item.get("expiry_date", "")
    today = datetime.today().date()
    expiry_soon = False

    if expiry_str:
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            if expiry_date < today:
                return {"text": "Expired", "className": "status-expired"}
            if (expiry_date - today).days <= EXPIRY_SOON_DAYS:
                expiry_soon = True
        except ValueError:
            pass

    if qty == 0:
        return {"text": "Out of Stock", "className": "status-out-of-stock"}
    if expiry_soon:
        return {"text": "Expiring Soon", "className": "status-expiring-soon"}
    if qty <= LOW_STOCK_THRESHOLD:
        return {"text": "Low Stock", "className": "status-low-stock"}
    return {"text": "In Stock", "className": "status-in-stock"}


def enrich_inventory(inv):
    for item in inv:
        item["status"] = get_item_status(item)
    return inv


# ------------------------------------------------------------------ #
#  DEMO DATA LOADERS
# ------------------------------------------------------------------ #
def load_demo_inventory():
    return enrich_inventory(load_csv(DEMO_INVENTORY))


def load_demo_sales():
    return load_csv(DEMO_SALES)


# ------------------------------------------------------------------ #
#  CURRENT USER DATA
# ------------------------------------------------------------------ #
def get_current_inventory():
    if session.get("is_demo"):
        return load_demo_inventory()
    return enrich_inventory(load_csv(inventory_file()))


def get_current_sales():
    if session.get("is_demo"):
        return load_demo_sales()
    return load_csv(sales_file())


# ------------------------------------------------------------------ #
#  USER MODEL
# ------------------------------------------------------------------ #
class User(UserMixin):
    def __init__(self, user_id, username, password_hash):
        self.id            = str(user_id)
        self.username      = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        for u in load_csv(USERS_FILE):
            if str(u["id"]) == str(user_id):
                return User(u["id"], u["username"], u["password_hash"])
        return None

    @staticmethod
    def get_by_username(username):
        for u in load_csv(USERS_FILE):
            if u["username"].lower() == username.lower():
                return User(u["id"], u["username"], u["password_hash"])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# ------------------------------------------------------------------ #
#  AUTH GUARD HELPER
# ------------------------------------------------------------------ #
def _require_auth():
    if not session.get("is_demo") and not current_user.is_authenticated:
        return redirect(url_for("login"))
    return None


# ================================================================== #
#  AUTH ROUTES
# ================================================================== #
@app.route("/try-demo")
def demo_login():
    session.clear()
    session["is_demo"] = True
    session["username"] = "Demo"
    return redirect(url_for("home"))


@app.route("/exit-demo")
def exit_demo():
    session.clear()
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        user = User.get_by_username(request.form.get("username", ""))
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("home"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users    = load_csv(USERS_FILE)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))

        if User.get_by_username(username):
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        new_id = max((int(u["id"]) for u in users), default=0) + 1
        users.append({
            "id":            new_id,
            "username":      username,
            "password_hash": generate_password_hash(password),
        })
        save_csv(USERS_FILE, users, ["id", "username", "password_hash"])

        inv_path   = os.path.join(BASE_DIR, f"{username}_inventory.csv")
        sales_path = os.path.join(BASE_DIR, f"{username}_sales.csv")
        save_csv(inv_path,   [], ["id", "name", "Manufacturer", "quantity", "price", "expiry_date"])
        save_csv(sales_path, [], ["bill_id", "date", "time", "product_name", "quantity", "unit_price", "total_amount"])

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for("login"))


# ================================================================== #
#  PAGE ROUTES
# ================================================================== #
@app.route("/")
def home():
    redir = _require_auth()
    if redir:
        return redir
    username = session.get("username") if session.get("is_demo") else current_user.username
    return render_template("index.html", username=username, is_demo=session.get("is_demo", False))


@app.route("/inventory")
def inventory_page():
    redir = _require_auth()
    if redir:
        return redir
    username = session.get("username") if session.get("is_demo") else current_user.username
    return render_template("inventory.html", username=username,
                           inventory=get_current_inventory(),
                           is_demo=session.get("is_demo", False))


@app.route("/sales")
def sales_page():
    redir = _require_auth()
    if redir:
        return redir
    username = session.get("username") if session.get("is_demo") else current_user.username
    return render_template("sales.html", username=username, is_demo=session.get("is_demo", False))


@app.route("/low_stock")
def low_stock_page():
    redir = _require_auth()
    if redir:
        return redir
    username  = session.get("username") if session.get("is_demo") else current_user.username
    inv       = get_current_inventory()
    low_items = [i for i in inv if int(i.get("quantity", 0)) <= LOW_STOCK_THRESHOLD]
    return render_template("low_stock.html", username=username,
                           low_stock_items=low_items,
                           is_demo=session.get("is_demo", False))


@app.route("/billing")
def billing_page():
    redir = _require_auth()
    if redir:
        return redir
    username = session.get("username") if session.get("is_demo") else current_user.username
    return render_template("billing.html", username=username, is_demo=session.get("is_demo", False))


@app.route("/account")
def account_page():
    redir = _require_auth()
    if redir:
        return redir
    username = session.get("username") if session.get("is_demo") else current_user.username
    return render_template("account.html", username=username, is_demo=session.get("is_demo", False))


# ================================================================== #
#  INVENTORY API
# ================================================================== #
@app.route("/api/inventory/all")
def api_inventory_all():
    if _require_auth():
        return jsonify([])
    return jsonify(get_current_inventory())


@app.route("/api/inventory/summary")
def api_inventory_summary():
    if _require_auth():
        return jsonify({})
    inv       = get_current_inventory()
    total_qty = sum(int(i.get("quantity", 0)) for i in inv)
    return jsonify({"total_items": len(inv), "total_quantity": total_qty})


@app.route("/api/inventory/low_stock")
def api_inventory_low_stock():
    if _require_auth():
        return jsonify({})
    inv       = get_current_inventory()
    low_items = [i for i in inv if int(i.get("quantity", 0)) <= LOW_STOCK_THRESHOLD]
    return jsonify({"low_stock_count": len(low_items), "items": low_items})


@app.route("/api/inventory/expiring_soon")
def api_inventory_expiring_soon():
    if _require_auth():
        return jsonify([])
    inv    = get_current_inventory()
    today  = datetime.today().date()
    cutoff = today + timedelta(days=EXPIRY_SOON_DAYS)
    result = []
    for item in inv:
        expiry_str = item.get("expiry_date", "")
        if expiry_str:
            try:
                exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if today <= exp <= cutoff:
                    result.append(item)
            except ValueError:
                pass
    result.sort(key=lambda x: x.get("expiry_date", ""))
    return jsonify(result)


@app.route("/api/inventory/status_distribution")
def api_inventory_status_distribution():
    if _require_auth():
        return jsonify({})
    inv   = get_current_inventory()
    total = len(inv) or 1
    counts = {"In Stock": 0, "Low Stock": 0, "Expiring Soon": 0,
              "Out of Stock": 0, "Expired": 0}
    for item in inv:
        text = item["status"]["text"]
        counts[text] = counts.get(text, 0) + 1
    return jsonify({
        "in_stock_percent":      round(counts["In Stock"]       / total * 100),
        "low_stock_percent":     round(counts["Low Stock"]       / total * 100),
        "expiring_soon_percent": round(counts["Expiring Soon"]   / total * 100),
        "out_of_stock_percent":  round((counts["Out of Stock"] + counts["Expired"]) / total * 100),
    })


@app.route("/api/inventory/search")
def api_inventory_search():
    if _require_auth():
        return jsonify([])
    q       = request.args.get("q", "").lower().strip()
    inv     = get_current_inventory()
    if not q:
        return jsonify(inv)
    results = [
        i for i in inv
        if q in i.get("name", "").lower() or q in i.get("Manufacturer", "").lower()
    ]
    return jsonify(results)


@app.route("/api/inventory/add", methods=["POST"])
def api_inventory_add():
    if session.get("is_demo"):
        return jsonify({"success": False, "message": "Demo mode: changes not saved."})
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    data = request.get_json(force=True)
    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    inv    = load_csv(inventory_file())
    new_id = max((int(i["id"]) for i in inv), default=0) + 1
    inv.append({
        "id":           new_id,
        "name":         data.get("name", "").strip(),
        "Manufacturer": data.get("Manufacturer", "").strip(),
        "quantity":     data.get("quantity", 0),
        "price":        data.get("price", 0),
        "expiry_date":  data.get("expiry_date", ""),
    })
    save_csv(inventory_file(), inv,
             ["id", "name", "Manufacturer", "quantity", "price", "expiry_date"])
    return jsonify({"success": True, "message": "Medicine added successfully."})


# ================================================================== #
#  SALES API
# ================================================================== #
def _filter_sales(sales, period):
    today = datetime.today().date()
    if period == "today":
        return [s for s in sales if s.get("date") == str(today)]
    if period == "monthly":
        prefix = today.strftime("%Y-%m")
        return [s for s in sales if s.get("date", "").startswith(prefix)]
    return sales


def _kpi_from_sales(sales):
    total_revenue      = sum(float(s.get("total_amount", 0)) for s in sales)
    total_transactions = len({s["bill_id"] for s in sales})
    total_items_sold   = sum(int(s.get("quantity", 0)) for s in sales)
    return {
        "total_revenue":      round(total_revenue, 2),
        "total_transactions": total_transactions,
        "total_items_sold":   total_items_sold,
    }


@app.route("/api/sales/summary")
def api_sales_summary():
    if _require_auth():
        return jsonify({})
    today_sales = _filter_sales(get_current_sales(), "today")
    return jsonify({"todays_sales": round(sum(float(s.get("total_amount", 0)) for s in today_sales), 2)})


@app.route("/api/sales/<period>")
def api_sales_by_period(period):
    if _require_auth():
        return jsonify([])
    if period not in ("today", "monthly", "all"):
        return jsonify({"error": "Invalid period"}), 400
    return jsonify(_filter_sales(get_current_sales(), period))


@app.route("/api/sales/kpi_summary/<period>")
def api_sales_kpi_summary(period):
    if _require_auth():
        return jsonify({})
    if period not in ("today", "monthly", "all"):
        return jsonify({"error": "Invalid period"}), 400
    return jsonify(_kpi_from_sales(_filter_sales(get_current_sales(), period)))


# ================================================================== #
#  BILLING API
# ================================================================== #
@app.route("/api/billing/create", methods=["POST"])
def api_billing_create():
    if session.get("is_demo"):
        return jsonify({"success": False, "message": "Demo mode: billing not available."})
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    data  = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify({"success": False, "message": "No items in bill."}), 400

    inv     = load_csv(inventory_file())
    sales   = load_csv(sales_file())
    inv_map = {str(i["id"]): i for i in inv}

    for item in items:
        inv_item = inv_map.get(str(item["id"]))
        if not inv_item:
            return jsonify({"success": False, "message": f"Item ID {item['id']} not found."}), 400
        if int(inv_item["quantity"]) < int(item["quantity"]):
            return jsonify({"success": False,
                            "message": f"Insufficient stock for '{inv_item['name']}'."}), 400

    bill_id  = max((int(s["bill_id"]) for s in sales), default=0) + 1
    now      = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    for item in items:
        inv_item   = inv_map[str(item["id"])]
        qty        = int(item["quantity"])
        unit_price = float(inv_item["price"])
        total      = round(qty * unit_price * 1.05, 2)

        sales.append({
            "bill_id":      bill_id,
            "date":         date_str,
            "time":         time_str,
            "product_name": inv_item["name"],
            "quantity":     qty,
            "unit_price":   unit_price,
            "total_amount": total,
        })
        inv_item["quantity"] = int(inv_item["quantity"]) - qty

    save_csv(sales_file(), sales,
             ["bill_id", "date", "time", "product_name", "quantity", "unit_price", "total_amount"])
    save_csv(inventory_file(), inv,
             ["id", "name", "Manufacturer", "quantity", "price", "expiry_date"])

    return jsonify({"success": True, "bill_id": bill_id,
                    "message": f"Bill #{bill_id} created successfully."})


# ================================================================== #
#  LEGACY FORM ROUTES
# ================================================================== #
@app.route("/add-inventory", methods=["POST"])
def add_inventory():
    if session.get("is_demo"):
        return redirect(url_for("home"))
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    inv    = load_csv(inventory_file())
    new_id = max((int(i["id"]) for i in inv), default=0) + 1
    inv.append({
        "id":           new_id,
        "name":         request.form.get("name", ""),
        "Manufacturer": request.form.get("Manufacturer", ""),
        "quantity":     request.form.get("quantity", 0),
        "price":        request.form.get("price", 0),
        "expiry_date":  request.form.get("expiry", ""),
    })
    save_csv(inventory_file(), inv,
             ["id", "name", "Manufacturer", "quantity", "price", "expiry_date"])
    return redirect(url_for("home"))


@app.route("/add-sale", methods=["POST"])
def add_sale():
    if session.get("is_demo"):
        return redirect(url_for("home"))
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    sales = load_csv(sales_file())
    now   = datetime.now()
    sales.append({
        "bill_id":      len(sales) + 1,
        "date":         now.strftime("%Y-%m-%d"),
        "time":         now.strftime("%H:%M:%S"),
        "product_name": request.form.get("product", ""),
        "quantity":     request.form.get("qty", 0),
        "unit_price":   request.form.get("price", 0),
        "total_amount": request.form.get("total", 0),
    })
    save_csv(sales_file(), sales,
             ["bill_id", "date", "time", "product_name", "quantity", "unit_price", "total_amount"])
    return redirect(url_for("home"))


# ================================================================== #
#  RUN
# ================================================================== #
if __name__ == "__main__":
    app.run(debug=True)
