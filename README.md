# Pharmacy Management System

VaultRx is a web-based dashboard application designed to help small pharmacies manage their inventory, sales, and billing. It provides a clean, user-friendly interface for pharmacists to track stock levels, process sales, and gain insights into their daily operations.

This project is built with a lightweight Python backend (Flask) and a dynamic frontend using plain JavaScript, HTML, and CSS.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

---

## Features

This application is built as a single-page-style dashboard with several key modules:

* **Main Dashboard:** Displays high-level Key Performance Indicators (KPIs) like:
    * Total Inventory Quantity
    * Low Stock Item Count
    * Today's Total Sales
    * A visual breakdown of inventory status (In Stock, Low Stock, etc.).
* **Inventory Management:**
    * View the complete inventory with details on price, quantity, and expiry date.
    * Dynamically calculates and displays the status of each item ("In Stock", "Low Stock", "Expiring Soon", "Out of Stock").
    * Add new medicines to the inventory via a pop-up modal.
* **Billing System:**
    * A dedicated page to create new customer bills.
    * Search for medicines from the inventory, which are then added to a dynamic bill.
    * Process sales, which automatically updates the inventory (decreases stock) and records the transaction in `sales.csv`.
* **Low Stock Report:** A separate page that filters and displays only the items that are currently low in stock (quantity of 20 or less).
* **Sales History:** A page to view all past sales transactions recorded by the system.
* **File-Based Database:** Uses simple `inventory.csv` and `sales.csv` files to store all data, making the project highly portable and easy to inspect.

---

## Technology Stack

* **Backend:**
    * **Python 3**
    * **Flask:** A lightweight web server to handle API requests and serve the HTML pages.
* **Frontend:**
    * **HTML5:** For the structure of all pages.
    * **CSS3:** For all custom styling, layout, and responsiveness.
    * **Vanilla JavaScript:** To handle all client-side interactivity, including:
        * Fetching data from the Flask API (`fetch`).
        * Dynamically creating and updating the billing table.
        * Showing and hiding the "Add Medicine" modal.
        * Updating the dashboard KPIs.
* **Database:**
    * **CSV Files:** (`inventory.csv`, `sales.csv`)

---

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You must have **Python 3** and **pip** installed on your machine.

### Installation & Running

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/](https://github.com/)prathamd24/Pharmacy-Management-System.git
    cd Pharmacy-Management-System
    ```

2.  **(Optional but Recommended) Create a Virtual Environment**
    ```sh
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    
    # For Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the necessary Python package**
    This project has one main dependency: Flask.
    ```sh
    pip install Flask
    ```

4.  **Run the Flask application**
    ```sh
    python app.py
    ```

5.  **View the project in your browser**
    Open your web browser and navigate to:
    ```
    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
    ```

    The application should now be running locally on your machine.
