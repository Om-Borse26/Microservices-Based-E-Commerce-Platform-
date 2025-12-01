from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import os
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ════════════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION - RDS Connection
# ════════════════════════════════════════════════════════════════════════════════

# Get database credentials from environment variables with RDS defaults
DB_HOST = os.getenv('DB_HOST', 'shopease-mysql-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ChangeMe123!')
DB_NAME = os.getenv('DB_NAME', 'shopeas')

# Build database URI
DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Configure SQLAlchemy - DIRECTLY USE DATABASE_URI (no os.getenv wrapper!)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

# ════════════════════════════════════════════════════════════════════════════════
# MICROSERVICES CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

PRODUCT_SERVICE_URL = os.getenv('http://product-service')
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service')

# ════════════════════════════════════════════════════════════════════════════════
# ORDER MODELS - Maps to 'orders' and 'order_items' tables in orderdb
# ════════════════════════════════════════════════════════════════════════════════

class Order(db.Model):
    __tablename__ = 'orders'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Changed from Float to Numeric
    status = db.Column(db.String(50), default='pending')
    payment_status = db.Column(db.String(50), default='pending')  # Added from RDS schema
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),  # Convert Decimal to float for JSON
            'status': self.status,
            'payment_status': self.payment_status,
            'shipping_address': self.shipping_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200))  # Added from RDS schema
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Changed from unit_price, Float to Numeric
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)  # Changed from total_price
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Added from RDS schema
    
    order = db.relationship('Order', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': float(self.price),  # Convert Decimal to float
            'subtotal': float(self.subtotal)
        }

# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def get_product_details(product_id):
    """Fetch product details from product service"""
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}', timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"⚠️  Failed to get product {product_id}: {e}", file=sys.stderr)
        return None

def validate_stock(product_id, quantity):
    """Check if product has sufficient stock"""
    product = get_product_details(product_id)
    if product and product.get('stock', 0) >= quantity:
        return True
    return False

# ════════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': 'order_service',
        'database': db_status,
        'db_name': DB_NAME,
        'db_host': DB_HOST
    }), 200

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()
        
        if not data or not data.get('user_id') or not data.get('items'):
            return jsonify({'error': 'User ID and items are required'}), 400
        
        # Validate all items and calculate total
        total_amount = 0
        validated_items = []
        
        for item in data['items']:
            if not all(k in item for k in ['product_id', 'quantity']):
                return jsonify({'error': 'Each item must have product_id and quantity'}), 400
            
            product = get_product_details(item['product_id'])
            if not product:
                return jsonify({'error': f'Product {item["product_id"]} not found'}), 404
            
            if not validate_stock(item['product_id'], item['quantity']):
                return jsonify({'error': f'Insufficient stock for product {item["product_id"]}'}), 400
            
            item_total = product['price'] * item['quantity']
            total_amount += item_total
            
            validated_items.append({
                'product_id': item['product_id'],
                'product_name': product['name'],
                'quantity': item['quantity'],
                'price': product['price'],
                'subtotal': item_total
            })
        
        # Create order
        order = Order(
            user_id=data['user_id'],
            total_amount=total_amount,
            shipping_address=data.get('shipping_address', '')
        )
        
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create order items
        for item_data in validated_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                price=item_data['price'],
                subtotal=item_data['subtotal']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Return order with items
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating order: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    try:
        order = Order.query.get_or_404(order_id)
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        # Enrich with product details
        for item in order_dict['items']:
            product = get_product_details(item['product_id'])
            if product:
                item['product_name'] = product['name']
                item['product_description'] = product.get('description', '')
        
        return jsonify(order_dict), 200
    except Exception as e:
        print(f"❌ Error getting order {order_id}: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 404

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Get all orders for a specific user"""
    try:
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        result = []
        
        for order in orders:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error getting user orders: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        if not data or not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {valid_statuses}'}), 400
        
        order.status = data['status']
        
        # Update payment_status if provided
        if 'payment_status' in data:
            order.payment_status = data['payment_status']
        
        order.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating order status: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """Get all orders (admin endpoint)"""
    try:
        status = request.args.get('status')
        
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        
        return jsonify({
            'orders': result,
            'count': len(result)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting all orders: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.status in ['shipped', 'delivered']:
            return jsonify({'error': 'Cannot cancel shipped or delivered orders'}), 400
        
        order.status = 'cancelled'
        order.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Order cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error cancelling order: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

# ════════════════════════════════════════════════════════════════════════════════
# FRONTEND SERVING ROUTES
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/frontend/<path:path>')
def serve_frontend(path):
    return send_from_directory('frontend', path)

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

# ════════════════════════════════════════════════════════════════════════════════
# APPLICATION STARTUP
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("="*80, file=sys.stderr)
    print("ORDER SERVICE STARTING", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Database: {DB_NAME}", file=sys.stderr)
    print(f"Host:     {DB_HOST}", file=sys.stderr)
    print(f"Port:     5002", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Product Service: {PRODUCT_SERVICE_URL}", file=sys.stderr)
    print(f"User Service:    {USER_SERVICE_URL}", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!", file=sys.stderr)
        except Exception as e:
            print(f"❌ Database connection failed: {e}", file=sys.stderr)
            print("⚠️  Service will start but may not function properly", file=sys.stderr)
    
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)