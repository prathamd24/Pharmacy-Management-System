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
            // Updated logic to correctly highlight sales link
            if (link.getAttribute('href') === '/sales' && currentPath === '/sales') {
                link.classList.add('active');
            } else if (link.getAttribute('href') !== '/sales' && link.getAttribute('href') === currentPath) {
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
        
        // Updated window.onclick to handle multiple modals
        window.onclick = (event) => {
            // Handle Add Medicine Modal
            if (modal && event.target == modal) {
                modal.style.display = 'none';
            }
            
            // Handle Expiring Soon Modal (if it exists on the page)
            const expiringSoonModal = document.getElementById('expiring-soon-modal');
            if (expiringSoonModal && event.target == expiringSoonModal) {
                expiringSoonModal.style.display = 'none';
            }

            // Handle Logout Modal (NEW)
            const logoutModal = document.getElementById('logout-confirm-modal');
            if (logoutModal && event.target == logoutModal) {
                logoutModal.style.display = 'none';
            }

            // Handle Billing Confirmation Modal
            const confirmationModal = document.getElementById('confirmation-modal');
             if (confirmationModal && event.target == confirmationModal) {
                confirmationModal.style.display = 'none';
            }
        };
    
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
                    
                    if (result.success) {
                        alert(result.message || 'Action completed successfully!');
                        modal.style.display = 'none';
                        form.reset();
                        // Reload page unless we are on the billing page
                        if (currentPath !== '/billing') {
                            location.reload();
                        }
                    } else {
                         alert(result.message || 'An error occurred.');
                    }
                } catch (error) {
                    console.error('Failed to add/update medicine:', error);
                    alert('An error occurred. Please try again.');
                }
            });
        }
        
        // --- (NEW) LOGOUT MODAL LOGIC ---
        const logoutBtn = document.getElementById('logout-btn-sidebar');
        const logoutModal = document.getElementById('logout-confirm-modal');
        const cancelLogoutBtn = document.getElementById('cancel-logout-btn');
        const logoutModalCloseBtn = document.querySelector('#logout-confirm-modal .close-btn');

        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault(); // Prevent default link behavior
                if (logoutModal) logoutModal.style.display = 'block';
            });
        }
        if (cancelLogoutBtn) {
            cancelLogoutBtn.addEventListener('click', () => {
                if (logoutModal) logoutModal.style.display = 'none';
            });
        }
        if (logoutModalCloseBtn) {
            logoutModalCloseBtn.addEventListener('click', () => {
                if (logoutModal) logoutModal.style.display = 'none';
            });
        }
        // --- END OF NEW LOGIC ---

    };

    setupUniversalComponents();

    // ===================================
    //  DASHBOARD PAGE ('/') LOGIC
    // ===================================
    if (currentPath === '/') {
        // Handle "View Expiring Soon" modal
        const expiringModal = document.getElementById('expiring-soon-modal');
        const expiringLink = document.getElementById('view-expiring-soon-link');
        const closeExpiringModal = document.getElementById('close-expiring-modal');

        if (expiringLink) {
            expiringLink.onclick = (e) => {
                e.preventDefault();
                // API call now uses 90 days
                fetch('/api/inventory/expiring_soon') 
                    .then(res => res.json())
                    .then(items => {
                        const tableBody = document.getElementById('expiring-soon-table-body');
                        tableBody.innerHTML = '';
                        if (items.length === 0) {
                            tableBody.innerHTML = '<tr><td colspan="6">No items are expiring soon.</td></tr>';
                        } else {
                            items.forEach(item => {
                                tableBody.innerHTML += `
                                    <tr>
                                        <td>${item.id}</td>
                                        <td>${item.name}</td>
                                        <td>${item.Manufacturer}</td>
                                        <td>${item.expiry_date}</td>
                                        <td>${item.quantity}</td>
                                        <td>${item.price}</td>
                                    </tr>
                                `;
                            });
                        }
                        expiringModal.style.display = 'block';
                    });
            }
        }

        if(closeExpiringModal) {
            closeExpiringModal.onclick = () => {
                expiringModal.style.display = 'none';
            }
        }
    
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
            if (!tableBody) return;
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
                    // Reset to full inventory if search is cleared
                    const tableBody = document.getElementById('full-inventory-table-body');
                    if(tableBody) tableBody.innerHTML = '';
                    displayedItemsCount = 0;
                    renderInventorySlice(); // Re-render the initial slice
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
        
        // Initial data fetches
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
    //  SALES REPORT PAGE LOGIC
    // ===================================
    if (currentPath === '/sales') {
        let currentSalesData = []; // Holds the data for searching
        const searchInput = document.getElementById('sales-search-input');
        const tableBody = document.getElementById('sales-table-body');
        const pageTitle = document.getElementById('page-title');
        const filterTabs = document.querySelectorAll('.filter-tab');

        // Re-usable function to render the table
        const renderSalesTable = (sales) => {
            if (!tableBody) return;
            tableBody.innerHTML = '';
            
            // Sort by Bill ID (newest first)
            sales.sort((a, b) => {
                const idA = parseInt(a.bill_id, 10);
                const idB = parseInt(b.bill_id, 10);
                return idB - idA;
            });

            if (sales.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6">No sales data found for this period.</td></tr>';
            } else {
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
            }
        };

        // Main function to load all data based on filter
        const loadSalesData = async (filter) => {
            // 1. Set active tab
            filterTabs.forEach(tab => {
                tab.classList.toggle('active', tab.dataset.filter === filter);
            });

            // 2. Update Page Title and KPI Labels
            const kpiLabels = {
                revenue: document.querySelector('#total-revenue-card-link p'),
                transactions: document.querySelector('#total-transactions-card-link p'),
                items: document.querySelector('#previous-sales-card-link p') // Note: ID seems mismatched, but following HTML
            };

            if (filter === 'today') {
                pageTitle.textContent = "Today's Sales";
                if(kpiLabels.revenue) kpiLabels.revenue.textContent = "Today's Revenue";
                if(kpiLabels.transactions) kpiLabels.transactions.textContent = "Today's Transactions";
                if(kpiLabels.items) kpiLabels.items.textContent = "Today's Items Sold";
            } else if (filter === 'monthly') { 
                pageTitle.textContent = "This Month's Sales";
                if(kpiLabels.revenue) kpiLabels.revenue.textContent = "This Month's Revenue";
                if(kpiLabels.transactions) kpiLabels.transactions.textContent = "This Month's Transactions";
                if(kpiLabels.items) kpiLabels.items.textContent = "This Month's Items Sold";
            } else if (filter === 'all') {
                pageTitle.textContent = "All Time Sales";
                if(kpiLabels.revenue) kpiLabels.revenue.textContent = "Total Revenue";
                if(kpiLabels.transactions) kpiLabels.transactions.textContent = "Total Transactions";
                if(kpiLabels.items) kpiLabels.items.textContent = "Total Items Sold";
            }

            // 3. Define endpoints based on filter
            let kpiEndpoint = `/api/sales/kpi_summary/${filter}`;
            let dataEndpoint = `/api/sales/${filter}`;

            // 4. Fetch and update KPIs
            try {
                const kpiResponse = await fetch(kpiEndpoint);
                const kpiData = await kpiResponse.json();
                document.getElementById('total-revenue').textContent = `₹${(kpiData.total_revenue || 0).toFixed(2)}`;
                document.getElementById('total-transactions').textContent = kpiData.total_transactions || 0;
                document.getElementById('total-items-sold').textContent = kpiData.total_items_sold || 0;
            } catch (error) {
                console.error(`Failed to load KPIs for ${filter}:`, error);
            }

            // 5. Fetch, store, and render table data
            try {
                const dataResponse = await fetch(dataEndpoint);
                currentSalesData = await dataResponse.json(); // Store for searching
                renderSalesTable(currentSalesData); // Render full data
                if (searchInput) searchInput.value = ''; // Clear search on tab change
            } catch (error) {
                console.error(`Failed to load sales data for ${filter}:`, error);
            }
        };

        // Add click handlers to filter tabs
        filterTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                loadSalesData(tab.dataset.filter);
            });
        });

        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('keyup', () => {
                const query = searchInput.value.toLowerCase().trim();
                const filteredData = currentSalesData.filter(sale => {
                    return sale.product_name.toLowerCase().includes(query) ||
                           sale.bill_id.toString().includes(query) ||
                           sale.date.includes(query);
                });
                renderSalesTable(filteredData);
            });
        }

        // Initial load (default to 'today')
        loadSalesData('today');
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

            if(subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
            if(gstEl) gstEl.textContent = `₹${gst.toFixed(2)}`;
            if(grandTotalEl) grandTotalEl.textContent = `₹${grandTotal.toFixed(2)}`;
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