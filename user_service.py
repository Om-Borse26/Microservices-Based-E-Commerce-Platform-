from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import requests
import os
import sys

app = Flask(__name__)
CORS(app)

# ════════════════════════════════════════════════════════════════════════════════
# SECRET KEY & JWT CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'shopease-secret-key-change-in-production')

# ════════════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION - RDS Connection
# ════════════════════════════════════════════════════════════════════════════════

DB_HOST = os.getenv('DB_HOST', 'shopease-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ChangeMe123!')
# keep the db name same for all services
DB_NAME = os.getenv('DB_NAME', 'shopease')

DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20
}

db = SQLAlchemy(app)

# ════════════════════════════════════════════════════════════════════════════════
# MICROSERVICES CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://shopease-alb-1528125855.us-east-1.elb.amazonaws.com/api/notifications')

# ════════════════════════════════════════════════════════════════════════════════
# USER MODEL
# ════════════════════════════════════════════════════════════════════════════════
    
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def send_notification(user_id, notification_type, message, email, username):
    try:
        response = requests.post(f'{NOTIFICATION_SERVICE_URL}',     
            json={
                'user_id': user_id,
                'type': notification_type,
                'category': 'user_registration' if notification_type == 'registration' else 'general',
                'title': 'Welcome to ShopEase!' if notification_type == 'registration' else 'Notification',
                'message': message,
                'email': email,
                'username': username,
                'delivery_method': 'email'
            },
            timeout=5
        )
        
        if response.status_code == 201:
            print(f"✅ Notification sent to user {user_id}", file=sys.stderr)
        else:
            print(f"⚠️  Notification failed: {response.status_code}", file=sys.stderr)
            
    except requests.RequestException as e:
        print(f"⚠️  Could not send notification: {e}", file=sys.stderr)

# ════════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
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

@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Missing required fields: username, email, password'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        send_notification(
            user.id,
            'registration',
            f'Welcome {user.username}! Your account has been created successfully.',
            user.email,
            user.username
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    print("USER SERVICE STARTING", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Database: {DB_NAME}", file=sys.stderr)
    print(f"Host:     {DB_HOST}", file=sys.stderr)
    print(f"Port:     5001", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    with app.app_context():
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                db.session.execute(db.text('SELECT 1'))
                print("✅ Database connection successful!", file=sys.stderr)
                
                try:
                    db.create_all()
                    print("✅ Database tables created/verified!", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️  Table creation warning: {e}", file=sys.stderr)
                
                break
                
            except Exception as e:
                retry_count += 1
                print(f"❌ Database connection attempt {retry_count}/{max_retries} failed: {e}", file=sys.stderr)
                
                if retry_count >= max_retries:
                    print(f"❌ Could not connect to database after {max_retries} attempts", file=sys.stderr)
                    print(f"   DB_HOST: {DB_HOST}", file=sys.stderr)
                    print(f"   DB_PORT: {DB_PORT}", file=sys.stderr)
                    print(f"   DB_USER: {DB_USER}", file=sys.stderr)
                    print(f"   DB_NAME: {DB_NAME}", file=sys.stderr)
                    print("⚠️  Service starting anyway but may not function properly", file=sys.stderr)
                else:
                    import time
                    time.sleep(2)
    
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)