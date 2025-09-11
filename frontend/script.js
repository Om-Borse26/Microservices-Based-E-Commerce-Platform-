// Global variables
let cart = [];
let allProducts = [];

// API Configuration
const API_BASE_URL = 'http://localhost:5000';

// Initialize the application
window.onload = function() {
    showSection('home');
    fetchProducts();
    updateCartDisplay();
};

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
    
    // Load products if products section is shown
    if (sectionName === 'products') {
        fetchProducts();
    }
    
    // Update cart display if cart section is shown
    if (sectionName === 'cart') {
        displayCartItems();
    }
}

// Product-related functions
function fetchProducts() {
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error-message');
    const productList = document.getElementById('product-list');
    
    if (loadingElement) loadingElement.style.display = 'block';
    if (errorElement) errorElement.style.display = 'none';
    
    fetch(`${API_BASE_URL}/products`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(products => {
            allProducts = products;
            displayProducts(products);
            if (loadingElement) loadingElement.style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching products:', error);
            if (loadingElement) loadingElement.style.display = 'none';
            if (errorElement) {
                errorElement.textContent = 'Failed to load products. Please try again later.';
                errorElement.style.display = 'block';
            }
            if (productList) {
                productList.innerHTML = '<p class="error">Could not load products. Please check if the server is running.</p>';
            }
        });
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

// Cart functions
function addToCart(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product || product.stock === 0) return;
    
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem) {
        if (existingItem.quantity < product.stock) {
            existingItem.quantity++;
        } else {
            alert('Cannot add more items. Stock limit reached.');
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
            alert('Cannot exceed stock limit.');
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

function checkout() {
    if (cart.length === 0) {
        alert('Your cart is empty!');
        return;
    }
    
    alert('Checkout functionality would be implemented here. Total: ₹' + 
          cart.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2));
}

// Admin functions
function addProduct(event) {
    event.preventDefault();
    
    const name = document.getElementById('product-name').value;
    const description = document.getElementById('product-description').value;
    const price = parseFloat(document.getElementById('product-price').value);
    const stock = parseInt(document.getElementById('product-stock').value);
    
    const productData = {
        name: name,
        description: description,
        price: price,
        stock: stock
    };
    
    fetch(`${API_BASE_URL}/products`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to add product');
        }
        return response.json();
    })
    .then(newProduct => {
        showNotification('Product added successfully!');
        document.getElementById('add-product-form').reset();
        fetchProducts(); // Refresh product list
    })
    .catch(error => {
        console.error('Error adding product:', error);
        alert('Failed to add product. Please try again.');
    });
}

// Utility functions
function showNotification(message) {
    // Create a simple notification
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
