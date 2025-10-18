// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;

    // --- UNIVERSAL LOGIC (for all pages) ---
    const setupUniversalComponents = () => {
        // Sidebar Toggle
        const menuBtn = document.getElementById('menu-btn');
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (menuBtn && dashboardContainer) {
            menuBtn.addEventListener('click', () => {
                dashboardContainer.classList.toggle('sidebar-hidden');
            });
        }

        // Active Navigation Link
        const navLinks = document.querySelectorAll('.sidebar-nav a');
        navLinks.forEach(link => {
            if ((link.getAttribute('href') === '/sales' || link.getAttribute('href') === '/previous_sales') && (currentPath === '/sales' || currentPath === '/previous_sales')) {
                link.classList.add('active');
            } else if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });

        // "Add Medicine" Modal
        const modal = document.getElementById('add-medicine-modal');
        const addBtnSidebar = document.getElementById('add-medicine-btn-sidebar');
        const closeBtn = document.querySelector('#add-medicine-modal .close-btn');
        const form = document.getElementById('add-medicine-form');

        if (addBtnSidebar) addBtnSidebar.onclick = () => { if (modal) modal.style.display = 'block'; };
        if (closeBtn) closeBtn.onclick = () => { if (modal) modal.style.display = 'none'; };
        window.onclick = (event) => { if (event.target == modal) modal.style.display = 'none'; };

        if (form) {
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const medicineData = {
                    name: document.getElementById('medicine-name').value,
                    Manufacturer: document.getElementById('Manufacturer-no').value,
                    expiry_date: document.getElementById('expiry-date').value,
                    quantity: document.getElementById('quantity').value,
                    price: document.getElementById('price').value,
                };

                try {
                    const response = await fetch('/api/inventory/add', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(medicineData)
                    });
                    const result = await response.json();
                    alert(result.message || 'Action completed successfully!');
                    if (result.success) {
                        modal.style.display = 'none';
                        form.reset();
                        if (currentPath !== '/billing') {
                            location.reload();
                        }
                    }
                } catch (error) {
                    console.error('Failed to add/update medicine:', error);
                    alert('An error occurred. Please try again.');
                }
            });
        }
    };

    setupUniversalComponents();

    // ===================================
    //  DASHBOARD PAGE ('/') LOGIC
    // ===================================
    if (currentPath === '/') {
        let fullInventory = [];
        let displayedItemsCount = 0;
        const itemsPerLoad = 5;

        // Element selectors
        const searchInput = document.getElementById('search-input');
        const fullInventorySection = document.getElementById('full-inventory-section');
        const lowStockCard = document.getElementById('low-stock-card');
        const inventoryCard = document.getElementById('total-inventory-card');
        const loadMoreBtn = document.getElementById('load-more-btn');

        const fetchKpiData = async () => {
            try {
                const [invRes, lowStockRes, salesRes] = await Promise.all([
                    fetch('/api/inventory/summary'),
                    fetch('/api/inventory/low_stock'),
                    fetch('/api/sales/summary')
                ]);
                const invSummary = await invRes.json();
                const lowStock = await lowStockRes.json();
                const salesSummary = await salesRes.json();

                document.getElementById('total-inventory-value').textContent = invSummary.total_quantity || 0;
                document.getElementById('low-stock-value').textContent = lowStock.low_stock_count || 0;
                document.getElementById('todays-sales-value').textContent = `₹${(salesSummary.todays_sales || 0).toFixed(2)}`;
            } catch (error) {
                console.error('Failed to load KPI data:', error);
            }
        };

        const fetchStatusDistribution = async () => {
            try {
                const response = await fetch('/api/inventory/status_distribution');
                const data = await response.json();
                document.getElementById('in-stock-percent').textContent = `${data.in_stock_percent || 0}%`;
                document.getElementById('low-stock-percent').textContent = `${data.low_stock_percent || 0}%`;
                document.getElementById('expiring-soon-percent').textContent = `${data.expiring_soon_percent || 0}%`;
                document.getElementById('out-of-stock-percent').textContent = `${data.out_of_stock_percent || 0}%`;
            } catch (error) {
                console.error('Failed to load status distribution:', error);
            }
        };

        const fetchExpiringSoon = async () => {
            try {
                const response = await fetch('/api/inventory/expiring_soon');
                const expiringSoon = await response.json();
                const tableBody = document.getElementById('inventory-table-body');
                if (!tableBody) return;

                tableBody.innerHTML = '';
                expiringSoon.slice(0, 5).forEach(item => {
                    const row = tableBody.insertRow();
                    row.innerHTML = `
                        <td>${item.name}</td>
                        <td>${item.Manufacturer}</td>
                        <td>${item.expiry_date}</td>
                        <td>${item.quantity}</td>
                        <td><span class="status-cell ${item.status.className}">${item.status.text}</span></td>
                    `;
                });
            } catch (error) {
                console.error('Failed to load expiring soon data:', error);
            }
        };

        const renderInventorySlice = () => {
            const tableBody = document.getElementById('full-inventory-table-body');
            const itemsToRender = fullInventory.slice(displayedItemsCount, displayedItemsCount + itemsPerLoad);

            itemsToRender.forEach(item => {
                const row = tableBody.insertRow();
                row.innerHTML = `
                    <td>${item.id}</td>
                    <td>${item.name}</td>
                    <td>${item.Manufacturer}</td>
                    <td>${item.expiry_date}</td>
                    <td>${item.quantity}</td>
                    <td><span class="status-cell ${item.status.className}">${item.status.text}</span></td>
                `;
            });

            displayedItemsCount += itemsToRender.length;

            if (loadMoreBtn) {
                loadMoreBtn.style.display = displayedItemsCount >= fullInventory.length ? 'none' : 'block';
            }
        };

        const fetchFullInventory = async () => {
            try {
                const response = await fetch('/api/inventory/all');
                fullInventory = await response.json();
                const tableBody = document.getElementById('full-inventory-table-body');
                if(tableBody) tableBody.innerHTML = '';
                displayedItemsCount = 0;
                renderInventorySlice();
            } catch (error) {
                console.error('Failed to load full inventory:', error);
            }
        };

        const renderFilteredInventory = (inventory) => {
            const tableBody = document.getElementById('full-inventory-table-body');
            if(!tableBody) return;
            tableBody.innerHTML = '';
            inventory.forEach(item => {
                const row = tableBody.insertRow();
                row.innerHTML = `
                    <td>${item.id}</td>
                    <td>${item.name}</td>
                    <td>${item.Manufacturer}</td>
                    <td>${item.expiry_date}</td>
                    <td>${item.quantity}</td>
                    <td><span class="status-cell ${item.status.className}">${item.status.text}</span></td>
                `;
            });
            if(loadMoreBtn) loadMoreBtn.style.display = 'none';
        };

        if (searchInput) {
            searchInput.addEventListener('keyup', async (event) => {
                // Scroll on Enter key press
                if (event.key === 'Enter') {
                    event.preventDefault();
                    if (fullInventorySection) {
                        fullInventorySection.scrollIntoView({ behavior: 'smooth' });
                    }
                }
                const query = event.target.value.toLowerCase();
                if (query.length > 2) {
                    try {
                        const response = await fetch(`/api/inventory/search?q=${query}`);
                        const filteredInventory = await response.json();
                        renderFilteredInventory(filteredInventory);
                    } catch (error) {
                        console.error('Search failed:', error);
                    }
                } else if (query.length === 0) {
                    fetchFullInventory();
                }
            });
        }
        
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', renderInventorySlice);
        }

        if (lowStockCard) {
            lowStockCard.addEventListener('click', () => {
                window.location.href = '/low_stock';
            });
        }
        
        // Add click event for inventory card to scroll
        if (inventoryCard && fullInventorySection) {
            inventoryCard.addEventListener('click', () => {
                fullInventorySection.scrollIntoView({ behavior: 'smooth' });
            });
        }
        
        fetchKpiData();
        fetchStatusDistribution();
        fetchExpiringSoon();
        fetchFullInventory();
    }

    // ===============================================
    //  INVENTORY & LOW STOCK PAGES LOGIC
    // ===============================================
    if (currentPath === '/inventory' || currentPath === '/low_stock') {
        const searchInput = document.getElementById('page-search-input');
        const tableBody = document.querySelector('.searchable-table tbody');

        if (searchInput && tableBody) {
            searchInput.addEventListener('keyup', () => {
                const query = searchInput.value.toLowerCase().trim();
                const rows = tableBody.querySelectorAll('tr');

                rows.forEach(row => {
                    const productName = row.cells[1].textContent.toLowerCase();
                    const manufacturer = row.cells[2].textContent.toLowerCase();
                    row.style.display = (productName.includes(query) || manufacturer.includes(query)) ? '' : 'none';
                });
            });
        }
    }

    // ===================================
    //  SALES & PREVIOUS SALES PAGE LOGIC
    // ===================================
    if (currentPath === '/sales' || currentPath === '/previous_sales') {
        let currentSalesData = [];
        const searchInput = document.getElementById('sales-search-input');
        const tableBody = document.getElementById('sales-table-body');
        const pageTitle = document.getElementById('page-title');

        const fetchSalesKpis = async (kpiEndpoint) => {
            try {
                const response = await fetch(kpiEndpoint);
                const data = await response.json();
                document.getElementById('total-revenue').textContent = `₹${(data.total_revenue || 0).toFixed(2)}`;
                document.getElementById('total-transactions').textContent = data.total_transactions || 0;
                document.getElementById('total-items-sold').textContent = data.total_items_sold || 0;
            } catch (error) {
                console.error('Failed to load sales KPIs:', error);
            }
        };

        const renderSalesTable = (sales) => {
            if (!tableBody) return;
            tableBody.innerHTML = '';
            sales.sort((a, b) => b.bill_id - a.bill_id);
            sales.forEach(sale => {
                const row = tableBody.insertRow();
                row.innerHTML = `
                    <td>#${sale.bill_id}</td>
                    <td>${sale.date} ${sale.time}</td>
                    <td>${sale.product_name}</td>
                    <td>${sale.quantity}</td>
                    <td>₹${parseFloat(sale.unit_price || 0).toFixed(2)}</td>
                    <td>₹${parseFloat(sale.total_amount || 0).toFixed(2)}</td>
                `;
            });
        };
        
        const fetchSalesData = async (dataEndpoint) => {
            try {
                const response = await fetch(dataEndpoint);
                currentSalesData = await response.json();
                renderSalesTable(currentSalesData);
            } catch (error) {
                console.error('Failed to load sales data:', error);
            }
        };

        const filterSales = () => {
            const query = searchInput.value.toLowerCase().trim();
            const filtered = query ? currentSalesData.filter(sale => 
                sale.bill_id.toString().includes(query) || 
                sale.product_name.toLowerCase().includes(query)
            ) : currentSalesData;
            renderSalesTable(filtered);
        };

        if (searchInput) {
            searchInput.addEventListener('keyup', filterSales);
        }

        if (currentPath === '/sales') {
            if (pageTitle) pageTitle.textContent = "Today's Sales";
            fetchSalesKpis('/api/sales/kpi_summary/today');
            fetchSalesData('/api/sales/today');
        } else { // /previous_sales
            if (pageTitle) pageTitle.textContent = "Previous Sales";
            fetchSalesKpis('/api/sales/kpi_summary/previous');
            fetchSalesData('/api/sales/previous/all');
            document.querySelector('#total-revenue-card-link p').textContent = "Previous Revenue";
            document.querySelector('#total-transactions-card-link p').textContent = "Previous Transactions";
            document.querySelector('#previous-sales-card-link p').textContent = "Previous Items Sold";
        }
    }
    
    // ===================================
    //  BILLING PAGE LOGIC
    // ===================================
    if (currentPath === '/billing') {
        const searchInput = document.getElementById('billing-search-input');
        const searchResults = document.getElementById('billing-search-results');
        const billItemsTableBody = document.getElementById('bill-items-body');
        const subtotalEl = document.getElementById('subtotal');
        const gstEl = document.getElementById('gst');
        const grandTotalEl = document.getElementById('grand-total');
        const processSaleBtn = document.getElementById('process-sale-btn');
        const clearBillBtn = document.getElementById('clear-bill-btn');
        
        const confirmationModal = document.getElementById('confirmation-modal');
        const confirmSaleBtn = document.getElementById('confirm-sale-btn');
        const cancelSaleBtn = document.getElementById('cancel-sale-btn');

        let billItems = [];
        let searchTimeout;

        const renderBillTable = () => {
            if (!billItemsTableBody) return;
            billItemsTableBody.innerHTML = '';
            let subtotal = 0;

            billItems.forEach((item, index) => {
                const total = parseFloat(item.price) * item.quantity;
                subtotal += total;

                const row = billItemsTableBody.insertRow();
                row.innerHTML = `
                    <td>${item.name}</td>
                    <td>₹${parseFloat(item.price).toFixed(2)}</td>
                    <td>
                        <input type="number" class="quantity-input" value="${item.quantity}" min="1" data-index="${index}">
                    </td>
                    <td>₹${total.toFixed(2)}</td>
                    <td><button class="remove-item-btn" data-index="${index}">&times;</button></td>
                `;
            });
            
            const gst = subtotal * 0.05;
            const grandTotal = subtotal + gst;

            subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
            gstEl.textContent = `₹${gst.toFixed(2)}`;
            grandTotalEl.textContent = `₹${grandTotal.toFixed(2)}`;
        };

        const performSearch = async () => {
            const query = searchInput.value.toLowerCase();
            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`/api/inventory/search?q=${query}`);
                const results = await response.json();
                
                searchResults.innerHTML = '';
                if (results.length > 0) {
                    results.forEach(item => {
                        if (parseInt(item.quantity) > 0) {
                            const div = document.createElement('div');
                            div.className = 'search-result-item';
                            div.innerHTML = `${item.name} <span class="text-light">(Stock: ${item.quantity})</span>`;
                            div.addEventListener('click', () => addToBill(item));
                            searchResults.appendChild(div);
                        }
                    });
                    searchResults.style.display = 'block';
                } else {
                    searchResults.style.display = 'none';
                }
            } catch (error) {
                console.error('Search failed:', error);
                searchResults.style.display = 'none';
            }
        };

        const addToBill = (item) => {
            const existingItem = billItems.find(billItem => billItem.id === item.id);
            if (existingItem) {
                if (existingItem.quantity < parseInt(item.maxStock)) {
                    existingItem.quantity++;
                } else {
                    alert('Maximum stock quantity reached for this item.');
                }
            } else {
                billItems.push({
                    id: item.id,
                    name: item.name,
                    price: item.price,
                    quantity: 1,
                    maxStock: parseInt(item.quantity)
                });
            }
            searchInput.value = '';
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
            renderBillTable();
        };
        
        const clearBill = () => {
            billItems = [];
            renderBillTable();
        };

        const processSale = async () => {
            if (billItems.length === 0) {
                alert('Cannot process an empty bill.');
                return;
            }
            if(confirmationModal) confirmationModal.style.display = 'flex';
        };

        const executeSale = async () => {
            try {
                const response = await fetch('/api/billing/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items: billItems })
                });
                const result = await response.json();
                if(confirmationModal) confirmationModal.style.display = 'none';

                if (result.success) {
                    alert(`Sale successful! Bill ID: ${result.bill_id}`);
                    clearBill();
                } else {
                    alert(result.message || 'An error occurred.');
                }
            } catch (error) {
                console.error('Sale processing failed:', error);
                alert('A critical error occurred. Please try again.');
                if(confirmationModal) confirmationModal.style.display = 'none';
            }
        };
        
        if (searchInput) {
            searchInput.addEventListener('keyup', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(performSearch, 300);
            });
        }
        
        if (billItemsTableBody) {
            billItemsTableBody.addEventListener('change', (e) => {
                if (e.target.classList.contains('quantity-input')) {
                    const index = e.target.dataset.index;
                    const newQty = parseInt(e.target.value);
                    const item = billItems[index];

                    if (newQty > item.maxStock) {
                        alert(`Only ${item.maxStock} units available in stock.`);
                        e.target.value = item.quantity;
                        return;
                    }
                    if (newQty > 0) billItems[index].quantity = newQty;
                    renderBillTable();
                }
            });
            billItemsTableBody.addEventListener('click', (e) => {
                if (e.target.classList.contains('remove-item-btn')) {
                    billItems.splice(e.target.dataset.index, 1);
                    renderBillTable();
                }
            });
        }

        if(processSaleBtn) processSaleBtn.addEventListener('click', processSale);
        if(clearBillBtn) clearBillBtn.addEventListener('click', clearBill);
        if(confirmSaleBtn) confirmSaleBtn.addEventListener('click', executeSale);
        if(cancelSaleBtn) cancelSaleBtn.addEventListener('click', () => {
            confirmationModal.style.display = 'none';
        });

        renderBillTable();
    }
});