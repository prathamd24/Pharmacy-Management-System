# 🏥 Pharmacy Management System (VaultRx)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

VaultRx is a web-based dashboard application designed to help small pharmacies manage their inventory, sales, and billing. It provides a clean, user-friendly interface for pharmacists to track stock levels, process sales, and gain insights into their daily operations.

**Live Demo:** [https://pharmacy-management-system-rlc4.onrender.com/](https://pharmacy-management-system-rlc4.onrender.com/)

---

## ✨ Features

This application is built as a single-page-style dashboard with several key modules:

* **📊 Main Dashboard:** Displays high-level Key Performance Indicators (KPIs) like Total Inventory Quantity, Low Stock Item Count, Today's Total Sales, and a visual breakdown of inventory status (In Stock, Low Stock, etc.).
* **💊 Inventory Management:** View the complete inventory with details on price, quantity, and expiry date. Dynamically calculates and displays the status of each item ("In Stock", "Low Stock", "Expiring Soon", "Out of Stock"). Add new medicines to the inventory via a modal.
* **🧾 Billing System:** Create new customer bills, search for medicines from the inventory, and process sales which automatically updates the inventory (decreases stock) and records the transaction.
* **⚠️ Low Stock Report:** Filter and display only the items that are currently low in stock.
* **📈 Sales History:** View all past sales transactions recorded by the system.
* **💾 File-Based Database:** Uses simple `.csv` files for each user to store all data, making the project highly portable.

---

## 💻 Technology Stack

* **Backend:** Python 3, Flask, Werkzeug
* **Frontend:** HTML5, CSS3 (Glassmorphism Dark Theme), Vanilla JavaScript
* **Database:** CSV Files (File-based DB)

---

## 🚀 Getting Started Locally

To get a local copy up and running, follow these steps.

### Prerequisites
You must have **Python 3** installed on your machine.

### Installation & Running

1. **Clone the repo**
   ```sh
   git clone https://github.com/prathamd24/Pharmacy-Management-System.git
   cd Pharmacy-Management-System
   ```

2. **Create a Virtual Environment & Activate**
   ```sh
   # For Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # For macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```sh
   python app.py
   ```

5. **View the project in your browser**
   Open your browser and navigate to: `http://127.0.0.1:5000/`

---

## ☁️ Deployment on Render

This project is fully configured to be deployed on Render as a Web Service. 

1. Create a new Web Service on Render and connect this GitHub repository.
2. Set the Build Command to: `pip install -r requirements.txt`
3. Set the Start Command to: `gunicorn app:app`
4. Deploy!
