import csv
import copy

def load_demo_inventory():
    inventory = []
    with open("demo_inventory.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory.append({
                "name": row["name"],
                "quantity": int(row["quantity"]),
                "price": float(row["price"])
            })
    return inventory


def load_demo_sales():
    sales = []
    with open("demo_sales.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sales.append({
                "medicine": row["medicine"],
                "qty": int(row["qty"]),
                "total": float(row["total"])
            })
    return sales
