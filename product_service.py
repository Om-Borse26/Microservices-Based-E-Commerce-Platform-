from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import os
import sys

app = Flask(__name__)
CORS(app)

# DB details
DB_HOST = os.getenv('DB_HOST', 'shopease-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ChangeMe123!')
# keep the db name same for all services
DB_NAME = os.getenv('DB_NAME', 'shopease')

DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'service': 'product_service', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            stock=data.get('stock', 0),
            category=data.get('category', ''),
            image_url=data.get('image_url', '')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'stock' in data:
            product.stock = data['stock']
        if 'category' in data:
            product.category = data['category']
        if 'image_url' in data:
            product.image_url = data['image_url']
        
        db.session.commit()
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>/stock', methods=['PATCH'])
def update_stock(product_id):
    try:
        data = request.get_json()
        product = Product.query.get_or_404(product_id)
        
        if 'quantity' in data:
            new_stock = product.stock + data['quantity']
            if new_stock < 0:
                return jsonify({'error': 'Insufficient stock'}), 400
            product.stock = new_stock
            db.session.commit()
            return jsonify(product.to_dict()), 200
        else:
            return jsonify({'error': 'Quantity required'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/init-data', methods=['POST'])
def init_data():
    """Initialize database with sample products"""
    try:
        # Check if products already exist
        if Product.query.count() > 0:
            return jsonify({'message': 'Products already exist'}), 200
        
        sample_products = [
            {
                'name': 'Laptop Pro',
                'description': 'High-performance laptop for professionals',
                'price': 1299.99,
                'stock': 50,
                'category': 'Electronics',
                'image_url': 'https://via.placeholder.com/300x300?text=Laptop+Pro'
            },
            {
                'name': 'Wireless Mouse',
                'description': 'Ergonomic wireless mouse',
                'price': 29.99,
                'stock': 200,
                'category': 'Electronics',
                'image_url': 'https://via.placeholder.com/300x300?text=Wireless+Mouse'
            },
            {
                'name': 'Office Chair',
                'description': 'Comfortable ergonomic office chair',
                'price': 199.99,
                'stock': 75,
                'category': 'Furniture',
                'image_url': 'https://via.placeholder.com/300x300?text=Office+Chair'
            },
            {
                'name': 'Standing Desk',
                'description': 'Adjustable height standing desk',
                'price': 399.99,
                'stock': 30,
                'category': 'Furniture',
                'image_url': 'https://via.placeholder.com/300x300?text=Standing+Desk'
            },
            {
                'name': 'Coffee Maker',
                'description': 'Programmable coffee maker',
                'price': 79.99,
                'stock': 100,
                'category': 'Appliances',
                'image_url': 'https://via.placeholder.com/300x300?text=Coffee+Maker'
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        return jsonify({'message': f'{len(sample_products)} products created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("PRODUCT SERVICE STARTING", file=sys.stderr)
    print(f"DB: {DB_HOST}/{DB_NAME}", file=sys.stderr)
    
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created", file=sys.stderr)
        except Exception as e:
            print(f"Database warning: {e}", file=sys.stderr)
    
    port = int(os.getenv('PORT', 5000))
    print(f"Starting server on port {port}", file=sys.stderr)
    app.run(debug=False, host='0.0.0.0', port=port)