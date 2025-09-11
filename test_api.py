import requests
import json

# Base URL for the product service
BASE_URL = 'http://localhost:5000'

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f"Health Check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def add_sample_products():
    """Add sample products to test the system"""
    sample_products = [
        {
            'name': 'Laptop',
            'description': 'High-performance laptop for work and gaming',
            'price': 75000.00,
            'stock': 10
        },
        {
            'name': 'Smartphone',
            'description': 'Latest smartphone with advanced features',
            'price': 25000.00,
            'stock': 25
        },
        {
            'name': 'Headphones',
            'description': 'Wireless noise-cancelling headphones',
            'price': 5000.00,
            'stock': 50
        },
        {
            'name': 'Tablet',
            'description': '10-inch tablet perfect for reading and browsing',
            'price': 20000.00,
            'stock': 15
        },
        {
            'name': 'Smart Watch',
            'description': 'Fitness tracking smartwatch with heart rate monitor',
            'price': 8000.00,
            'stock': 30
        }
    ]
    
    for product in sample_products:
        try:
            response = requests.post(
                f'{BASE_URL}/products',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(product)
            )
            if response.status_code == 201:
                print(f"✅ Added: {product['name']}")
            else:
                print(f"❌ Failed to add {product['name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error adding {product['name']}: {e}")

def test_get_products():
    """Test getting all products"""
    try:
        response = requests.get(f'{BASE_URL}/products')
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Found {len(products)} products:")
            for product in products:
                print(f"  - {product['name']}: ₹{product['price']}")
        else:
            print(f"❌ Failed to get products: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting products: {e}")

if __name__ == '__main__':
    print("🧪 Testing Product Service...")
    print("=" * 50)
    
    # Test health endpoint
    if test_health():
        print("✅ Service is healthy!")
        
        # Add sample products
        print("\n📦 Adding sample products...")
        add_sample_products()
        
        # Test getting products
        print("\n📋 Testing product retrieval...")
        test_get_products()
        
        print("\n🎉 Test completed! You can now open http://localhost:5000 in your browser.")
    else:
        print("❌ Service is not responding. Make sure it's running on port 5000.")
