from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
import requests
from functools import wraps

app = Flask(__name__)
CORS(app)

# ════════════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION - RDS Connection
# ════════════════════════════════════════════════════════════════════════════════

DB_HOST = os.getenv('DB_HOST', 'shopease-mysql-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Yog101619Admin')
DB_NAME = os.getenv('DB_NAME', 'userdb')

DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', DATABASE_URI)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production-12345')

db = SQLAlchemy(app)

# ════════════════════════════════════════════════════════════════════════════════
# MICROSERVICES CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:5004')

# ════════════════════════════════════════════════════════════════════════════════
# USER MODEL - Maps to 'users' table in userdb
# ════════════════════════════════════════════════════════════════════════════════

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

# ════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION DECORATOR
# ════════════════════════════════════════════════════════════════════════════════

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# ════════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': 'user_service',
        'database': db_status,
        'db_name': DB_NAME,
        'db_host': DB_HOST
    }), 200

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email notification
        try:
            notification_data = {
                'user_id': user.id,
                'type': 'email',
                'category': 'user_registration',
                'title': 'Welcome to ShopEase!',
                'message': f'Welcome {user.first_name or user.username}! Your account has been created successfully.',
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            
            response = requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json=notification_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Welcome email sent successfully for user {user.username}")
            else:
                print(f"⚠️  Welcome email failed with status {response.status_code}")
                
        except Exception as email_error:
            print(f"⚠️  Welcome email failed: {email_error}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']) and user.is_active:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get user by ID - for inter-service communication"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': 'User not found'}), 404

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    """Get current user profile"""
    try:
        user = User.query.get_or_404(current_user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user_id):
    """Update current user profile"""
    try:
        user = User.query.get_or_404(current_user_id)
        data = request.get_json()
        
        if data.get('email'):
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user_id:
                return jsonify({'error': 'Email already exists'}), 409
            user.email = data['email']
        
        if data.get('first_name'):
            user.first_name = data['first_name']
        
        if data.get('last_name'):
            user.last_name = data['last_name']
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users (admin endpoint)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
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
    print("="*80)
    print("USER SERVICE STARTING")
    print("="*80)
    print(f"Database: {DB_NAME}")
    print(f"Host:     {DB_HOST}")
    print(f"Port:     5001")
    print("="*80)
    print(f"Notification Service: {NOTIFICATION_SERVICE_URL}")
    print("="*80)
    
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Service will start but may not function properly")
    
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)