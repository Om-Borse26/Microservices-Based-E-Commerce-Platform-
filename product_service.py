from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'shopease-mysql-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Yog101619Admin')
DB_NAME = os.getenv('DB_NAME', 'productdb')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'category': self.category,
            'stock': self.stock,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Health check
@app.route('/health', methods=['GET'])
def health():
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'service': 'product-service',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'product-service',
            'database': 'disconnected',
            'error': str(e)
        }), 503

# Get all products
@app.route('/products', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category')
        
        if category:
            products = Product.query.filter_by(category=category).all()
        else:
            products = Product.query.all()
        
        return jsonify({
            'products': [product.to_dict() for product in products],
            'count': len(products)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get product by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Create product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category=data.get('category'),
            stock=data.get('stock', 0),
            image_url=data.get('image_url')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update product
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.category = data.get('category', product.category)
        product.stock = data.get('stock', product.stock)
        product.image_url = data.get('image_url', product.image_url)
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("="*80)
    print("PRODUCT SERVICE STARTING")
    print("="*80)
    print(f"Database: {DB_NAME} @ {DB_HOST}")
    print(f"Port: 5000")
    print("="*80)
    
    with app.app_context():
        try:
            # Test connection
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)