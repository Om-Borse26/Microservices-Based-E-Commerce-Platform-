from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Database via env var with fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:Yog%40101619@localhost/orderdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuration for other microservices via env
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5000')
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')

# Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Reference to user service
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    shipping_address = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'shipping_address': self.shipping_address
        }

# Order Item Model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # Reference to product service
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }

# Helper functions
def get_product_details(product_id):
    """Fetch product details from product service"""
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}')
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None

def validate_stock(product_id, quantity):
    """Check if product has sufficient stock"""
    product = get_product_details(product_id)
    if product and product['stock'] >= quantity:
        return True
    return False

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'service': 'order_service'}), 200

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
                'quantity': item['quantity'],
                'unit_price': product['price'],
                'total_price': item_total
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
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Return order with items
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 201
        
    except Exception as e:
        db.session.rollback()
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
                item['product_description'] = product['description']
        
        return jsonify(order_dict), 200
    except Exception as e:
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
        order.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """Get all orders (admin endpoint)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        orders = Order.query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for order in orders.items:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        
        return jsonify({
            'orders': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': orders.total,
                'pages': orders.pages
            }
        }), 200
        
    except Exception as e:
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
        return jsonify({'error': str(e)}), 500

@app.route('/frontend/<path:path>')
def serve_frontend(path):
    return send_from_directory('frontend', path)

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
