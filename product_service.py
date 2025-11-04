from flask import Flask, request, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Database via env var with fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:Yog%40101619@localhost/productdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock
        }

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'service': 'product_service'}), 200

@app.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    try:
        product = Product.query.get_or_404(id)
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('price'):
            return jsonify({'error': 'Name and Price are required'}), 400
        
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            stock=data.get('stock', 0)
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.stock = data.get('stock', product.stock)
    db.session.commit()
    return jsonify(product.to_dict()), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return '', 204

@app.route('/init-data', methods=['POST'])
def init_sample_data():
    """Initialize database with sample products"""
    try:
        # Check if products already exist
        if Product.query.count() > 0:
            return jsonify({'message': 'Sample data already exists'}), 200
        
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
        
        for product_data in sample_products:
            product = Product(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock']
            )
            db.session.add(product)
        
        db.session.commit()
        return jsonify({'message': 'Sample data created successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/frontend/<path:path>')
def serve_frontend(path):
    return send_from_directory('frontend', path)

@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend', 'style.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('frontend', 'script.js')

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)

# Test Jenkins build
