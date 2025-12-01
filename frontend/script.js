// Global variables
let cart = [];
let allProducts = [];
let currentUser = null;
let authToken = null;
let currentOrderId = null;

// API Configuration
const ALB_BASE_URL = 'http://shopease-alb-1528125855.us-east-1.elb.amazonaws.com';

const API_SERVICES = {
    product: `${ALB_BASE_URL}/api/products`,
    user: `${ALB_BASE_URL}/api/users`,
    order: `${ALB_BASE_URL}/api/orders`,
    payment: `${ALB_BASE_URL}/api/payments`,
    notification: `${ALB_BASE_URL}/api/notifications`
};

// Initialize the application
window.onload = function() {
    checkLoginStatus();
    showSection('home');
    fetchProducts();
    updateCartDisplay();
};

// Authentication functions
function checkLoginStatus() {
    const savedUser = localStorage.getItem('currentUser');
    const savedToken = localStorage.getItem('authToken');
    
    if (savedUser && savedToken) {
        currentUser = JSON.parse(savedUser);
        authToken = savedToken;
        updateUIForLoggedInUser();
    }
}

function updateUIForLoggedInUser() {
    document.getElementById('user-greeting').textContent = `Hello, ${currentUser.first_name}!`;
    document.getElementById('user-greeting').style.display = 'inline';
    document.getElementById('login-link').style.display = 'none';
    document.getElementById('register-link').style.display = 'none';
    document.getElementById('logout-link').style.display = 'inline';
    document.getElementById('orders-link').style.display = 'inline';
}

function updateUIForLoggedOutUser() {
    document.getElementById('user-greeting').style.display = 'none';
    document.getElementById('login-link').style.display = 'inline';
    document.getElementById('register-link').style.display = 'inline';
    document.getElementById('logout-link').style.display = 'none';
    document.getElementById('orders-link').style.display = 'none';
}

async function register(event) {
    event.preventDefault();
    
    const userData = {
        username: document.getElementById('register-username').value,
        email: document.getElementById('register-email').value,
        password: document.getElementById('register-password').value,
        first_name: document.getElementById('register-firstname').value,
        last_name: document.getElementById('register-lastname').value
    };
    
    try {
        const response = await fetch(`${API_SERVICES.user}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Registration successful! Please login.');
            showSection('login');
            document.getElementById('register-form').reset();
        } else {
            showNotification(result.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showNotification('Network error during registration', 'error');
    }
}

async function login(event) {
    event.preventDefault();
    
    const loginData = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value
    };
    
    try {
        const response = await fetch(`${API_SERVICES.user}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUser = result.user;
            authToken = result.token;
            
            // Store in localStorage
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            localStorage.setItem('authToken', authToken);
            
            updateUIForLoggedInUser();
            showNotification(`Welcome back, ${currentUser.first_name}!`);
            showSection('products');
            document.getElementById('login-form').reset();
        } else {
            showNotification(result.error || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Network error during login', 'error');
    }
}

function logout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');
    updateUIForLoggedOutUser();
    cart = [];
    updateCartDisplay();
    showNotification('Logged out successfully');
    showSection('home');
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.style.display = 'none');
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    // Load appropriate data
    if (sectionName === 'products') {
        fetchProducts();
    } else if (sectionName === 'cart') {
        displayCartItems();
    } else if (sectionName === 'orders' && currentUser) {
        fetchUserOrders();
    } else if (sectionName === 'admin') {
        loadAdminData();
    }
}

// Product functions (existing code enhanced)
async function fetchProducts() {
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error-message');
    const productList = document.getElementById('product-list');
    
    if (loadingElement) loadingElement.style.display = 'block';
    if (errorElement) errorElement.style.display = 'none';
    
    try {
        const response = await fetch(`${API_SERVICES.product}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const products = await response.json();
        allProducts = products;
        displayProducts(products);
        if (loadingElement) loadingElement.style.display = 'none';
    } catch (error) {
        console.error('Error fetching products:', error);
        if (loadingElement) loadingElement.style.display = 'none';
        if (errorElement) {
            errorElement.textContent = 'Failed to load products. Please try again later.';
            errorElement.style.display = 'block';
        }
    }
}

function displayProducts(products) {
    const productList = document.getElementById('product-list');
    if (!productList) return;
    
    productList.innerHTML = '';
    
    if (products.length === 0) {
        productList.innerHTML = '<p class="no-products">No products found.</p>';
        return;
    }
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div class="product-info">
                <h3>${product.name}</h3>
                <p class="product-description">${product.description || 'No description available'}</p>
                <p class="product-price"><strong>₹${product.price}</strong></p>
                <p class="product-stock">Stock: ${product.stock}</p>
            </div>
            <div class="product-actions">
                <button onclick="addToCart(${product.id})" 
                        ${product.stock === 0 ? 'disabled' : ''} 
                        class="add-to-cart-btn">
                    ${product.stock === 0 ? 'Out of Stock' : 'Add to Cart'}
                </button>
            </div>
        `;
        productList.appendChild(card);
    });
}

function searchProducts() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const filteredProducts = allProducts.filter(product => 
        product.name.toLowerCase().includes(searchTerm) ||
        (product.description && product.description.toLowerCase().includes(searchTerm))
    );
    displayProducts(filteredProducts);
}

// Cart functions (enhanced)
function addToCart(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product || product.stock === 0) return;
    
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        if (existingItem.quantity < product.stock) {
            existingItem.quantity++;
        } else {
            showNotification('Cannot add more items. Stock limit reached.', 'error');
            return;
        }
    } else {
        cart.push({...product, quantity: 1});
    }
    
    updateCartDisplay();
    showNotification('Product added to cart!');
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartDisplay();
    displayCartItems();
}

function updateQuantity(productId, newQuantity) {
    const item = cart.find(item => item.id === productId);
    const product = allProducts.find(p => p.id === productId);
    
    if (item && product) {
        if (newQuantity <= 0) {
            removeFromCart(productId);
        } else if (newQuantity <= product.stock) {
            item.quantity = newQuantity;
            updateCartDisplay();
            displayCartItems();
        } else {
            showNotification('Cannot exceed stock limit.', 'error');
        }
    }
}

function updateCartDisplay() {
    const cartCount = document.getElementById('cart-count');
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (cartCount) cartCount.textContent = totalItems;
}

function displayCartItems() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    
    if (!cartItems || !cartTotal) return;
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="empty-cart">Your cart is empty.</p>';
        cartTotal.textContent = '0';
        return;
    }
    
    cartItems.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-item';
        itemElement.innerHTML = `
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <p>₹${item.price} each</p>
            </div>
            <div class="cart-item-controls">
                <button onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                <span class="quantity">${item.quantity}</span>
                <button onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                <button onclick="removeFromCart(${item.id})" class="remove-btn">Remove</button>
            </div>
            <div class="cart-item-total">
                ₹${(item.price * item.quantity).toFixed(2)}
            </div>
        `;
        cartItems.appendChild(itemElement);
        total += item.price * item.quantity;
    });
    
    cartTotal.textContent = total.toFixed(2);
}

// Enhanced checkout function that uses Order Service
async function checkout() {
    if (!currentUser) {
        showNotification('Please login to place an order', 'error');
        showSection('login');
        return;
    }
    
    if (cart.length === 0) {
        showNotification('Your cart is empty!', 'error');
        return;
    }
    
    const shippingAddress = document.getElementById('shipping-address').value.trim();
    if (!shippingAddress) {
        showNotification('Please enter shipping address', 'error');
        return;
    }
    
    try {
        // Create order using Order Service
        const orderData = {
            user_id: currentUser.id,
            items: cart.map(item => ({
                product_id: item.id,
                quantity: item.quantity
            })),
            shipping_address: shippingAddress
        };
        
        const orderResponse = await fetch(`${API_SERVICES.order}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        
        if (!orderResponse.ok) {
            const error = await orderResponse.json();
            throw new Error(error.error || 'Order creation failed');
        }
        
        const order = await orderResponse.json();
        currentOrderId = order.id;
        
        showNotification('Order created successfully! Proceeding to payment...');
        
        // Show payment modal
        document.getElementById('payment-amount').textContent = order.total_amount.toFixed(2);
        document.getElementById('payment-modal').style.display = 'block';
        
    } catch (error) {
        showNotification(`Order creation failed: ${error.message}`, 'error');
    }
}

// Payment processing function
async function processPayment(event) {
    event.preventDefault();
    
    const paymentMethod = document.querySelector('input[name="payment-method"]:checked').value;
    const totalAmount = parseFloat(document.getElementById('payment-amount').textContent);
    
    const paymentData = {
        order_id: currentOrderId,
        user_id: currentUser.id,
        amount: totalAmount,
        payment_method: paymentMethod
    };
    
    // Add card details if card payment
    if (paymentMethod === 'card') {
        paymentData.card_details = {
            number: document.getElementById('card-number').value,
            expiry: document.getElementById('card-expiry').value,
            cvv: document.getElementById('card-cvv').value,
            name: document.getElementById('card-name').value,
            brand: 'Visa' // You can detect this from card number
        };
    }
    
    try {
        const paymentResponse = await fetch(`${API_SERVICES.payment}/payments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(paymentData)
        });
        
        const paymentResult = await paymentResponse.json();
        
        if (paymentResponse.ok && paymentResult.payment_status === 'completed') {
            showNotification('Payment successful! Order confirmed.');
            
            // Clear cart
            cart = [];
            updateCartDisplay();
            
            // Close modal
            closePaymentModal();
            
            // Show order confirmation
            showSection('orders');
            fetchUserOrders();
            
        } else {
            showNotification('Payment failed. Please try again.', 'error');
        }
        
    } catch (error) {
        showNotification(`Payment processing error: ${error.message}`, 'error');
    }
}

function closePaymentModal() {
    document.getElementById('payment-modal').style.display = 'none';
    document.getElementById('payment-form').reset();
}

// Order management functions
async function fetchUserOrders() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_SERVICES.order}/orders/user/${currentUser.id}`);
        const orders = await response.json();
        
        displayUserOrders(orders);
    } catch (error) {
        console.error('Error fetching orders:', error);
    }
}

function displayUserOrders(orders) {
    const ordersList = document.getElementById('orders-list');
    if (!ordersList) return;
    
    if (orders.length === 0) {
        ordersList.innerHTML = '<p>You have no orders yet.</p>';
        return;
    }
    
    ordersList.innerHTML = '';
    
    orders.forEach(order => {
        const orderElement = document.createElement('div');
        orderElement.className = 'order-item';
        orderElement.innerHTML = `
            <div class="order-header">
                <h3>Order #${order.id}</h3>
                <span class="order-status status-${order.status}">${order.status.toUpperCase()}</span>
            </div>
            <div class="order-details">
                <p><strong>Total:</strong> ₹${order.total_amount}</p>
                <p><strong>Date:</strong> ${new Date(order.created_at).toLocaleDateString()}</p>
                <p><strong>Items:</strong> ${order.items ? order.items.length : 0} items</p>
            </div>
        `;
        ordersList.appendChild(orderElement);
    });
}

// Admin functions
function showAdminTab(tabName) {
    // Hide all admin tabs
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`admin-${tabName}`).style.display = 'block';
    event.target.classList.add('active');
    
    // Load appropriate data
    if (tabName === 'orders') {
        loadAllOrders();
    } else if (tabName === 'users') {
        loadAllUsers();
    } else if (tabName === 'payments') {
        loadPaymentStats();
    }
}

async function loadAdminData() {
    // Load default admin tab data
    loadAllOrders();
}

async function loadAllOrders() {
    try {
        const response = await fetch(`${API_SERVICES.order}/orders`);
        const data = await response.json();
        const orders = data.orders || data;
        
        const ordersList = document.getElementById('admin-orders-list');
        if (orders.length === 0) {
            ordersList.innerHTML = '<p>No orders found.</p>';
            return;
        }
        
        ordersList.innerHTML = orders.map(order => `
            <div class="admin-order-item">
                <h4>Order #${order.id}</h4>
                <p>User ID: ${order.user_id} | Total: ₹${order.total_amount} | Status: ${order.status}</p>
                <p>Date: ${new Date(order.created_at).toLocaleDateString()}</p>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

async function loadAllUsers() {
    try {
        const response = await fetch(`${API_SERVICES.user}/users`);
        const users = await response.json();
        
        const usersList = document.getElementById('admin-users-list');
        usersList.innerHTML = users.map(user => `
            <div class="admin-user-item">
                <h4>${user.first_name} ${user.last_name}</h4>
                <p>Username: ${user.username} | Email: ${user.email}</p>
                <p>Joined: ${new Date(user.created_at).toLocaleDateString()}</p>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadPaymentStats() {
    try {
        const response = await fetch(`${API_SERVICES.payment}/payments/stats`);
        const stats = await response.json();
        
        const statsContainer = document.getElementById('admin-payments-stats');
        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <h4>Total Payments</h4>
                    <p>${stats.total_payments}</p>
                </div>
                <div class="stat-item">
                    <h4>Successful Payments</h4>
                    <p>${stats.completed_payments}</p>
                </div>
                <div class="stat-item">
                    <h4>Success Rate</h4>
                    <p>${stats.success_rate}%</p>
                </div>
                <div class="stat-item">
                    <h4>Total Revenue</h4>
                    <p>₹${stats.total_revenue}</p>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading payment stats:', error);
    }
}

// Enhanced product addition for admin
async function addProduct(event) {
    event.preventDefault();
    
    const productData = {
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value,
        price: parseFloat(document.getElementById('product-price').value),
        stock: parseInt(document.getElementById('product-stock').value)
    };
    
    try {
        const response = await fetch(`${API_SERVICES.product}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        
        if (response.ok) {
            showNotification('Product added successfully!');
            document.getElementById('add-product-form').reset();
            fetchProducts(); // Refresh product list
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to add product', 'error');
        }
    } catch (error) {
        showNotification('Network error while adding product', 'error');
    }
}

// Utility functions
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
