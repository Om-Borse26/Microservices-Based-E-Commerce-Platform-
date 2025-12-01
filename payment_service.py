from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import uuid
import random
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
DB_NAME = os.getenv('DB_NAME', 'shopease')

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

ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service')
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service')

# ════════════════════════════════════════════════════════════════════════════════
# PAYMENT MODEL - Maps to 'payments' table in paymentdb
# ════════════════════════════════════════════════════════════════════════════════

class Payment(db.Model):
    __tablename__ = 'payments'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Changed from Float to Numeric
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': float(self.amount),  # Convert Decimal to float for JSON
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def generate_payment_id():
    """Generate unique payment ID"""
    return f"PAY_{uuid.uuid4().hex[:12].upper()}"

def generate_transaction_id():
    """Generate mock transaction ID"""
    return f"TXN_{uuid.uuid4().hex[:16].upper()}"

def simulate_payment_gateway(payment_method, amount, card_details=None):
    """Simulate payment gateway processing"""
    import time
    time.sleep(0.5)  # Reduced from 1 second
    
    # Simulate random success/failure (90% success rate)
    success_rate = 0.9
    is_successful = random.random() < success_rate
    
    if is_successful:
        return {
            'status': 'success',
            'transaction_id': generate_transaction_id(),
            'message': 'Payment processed successfully',
            'gateway_fee': round(float(amount) * 0.02, 2)  # 2% gateway fee
        }
    else:
        return {
            'status': 'failed',
            'transaction_id': generate_transaction_id(),
            'message': 'Payment failed due to insufficient funds',
            'error_code': 'INSUFFICIENT_FUNDS'
        }

def update_order_status(order_id, status):
    """Update order status in order service"""
    try:
        response = requests.put(
            f'{ORDER_SERVICE_URL}/orders/{order_id}/status',
            headers={'Content-Type': 'application/json'},
            json={'status': status},
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"⚠️  Failed to update order status: {e}", file=sys.stderr)
        return False

def send_payment_notification(user_id, payment_data, order_id):
    """Send payment notification via notification service"""
    try:
        # Try to get user details from user service
        user_email = None
        user_name = "Customer"
        
        try:
            user_response = requests.get(f'{USER_SERVICE_URL}/users/{user_id}', timeout=5)
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_email = user_data.get('email')
                user_name = user_data.get('first_name') or user_data.get('username', 'Customer')
        except requests.RequestException:
            print(f"⚠️  Could not get user details from user service for user_id {user_id}", file=sys.stderr)
        
        notification_data = {
            'user_id': user_id,
            'type': 'payment',
            'category': 'payment_confirmation',
            'title': f'Payment Confirmation - Order #{order_id}',
            'message': f"Payment of ₹{payment_data['amount']} for Order #{order_id} has been {payment_data['payment_status']}",
            'delivery_method': 'email',
            'status': 'pending'
        }
        
        if user_email:
            notification_data['email'] = user_email
        
        response = requests.post(
            f'{NOTIFICATION_SERVICE_URL}/notifications',
            headers={'Content-Type': 'application/json'},
            json=notification_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Payment notification sent successfully", file=sys.stderr)
            return True
        else:
            print(f"⚠️  Payment notification failed with status {response.status_code}", file=sys.stderr)
            return False
            
    except requests.RequestException as e:
        print(f"❌ Payment notification failed: {str(e)}", file=sys.stderr)
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
        'service': 'payment_service',
        'database': db_status,
        'db_name': DB_NAME,
        'db_host': DB_HOST
    }), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    """Process a new payment"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['order_id', 'user_id', 'amount', 'payment_method']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: order_id, user_id, amount, payment_method'}), 400
        
        # Process payment through gateway
        gateway_response = simulate_payment_gateway(
            data['payment_method'], 
            data['amount'], 
            data.get('card_details')
        )
        
        # Create payment record
        payment = Payment(
            order_id=data['order_id'],
            user_id=data['user_id'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            payment_status='completed' if gateway_response['status'] == 'success' else 'failed',
            transaction_id=gateway_response.get('transaction_id')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Update order status
        order_status = 'confirmed' if payment.payment_status == 'completed' else 'pending'
        update_order_status(payment.order_id, order_status)
        
        # Send notification
        send_payment_notification(payment.user_id, payment.to_dict(), payment.order_id)
        
        response_data = payment.to_dict()
        response_data['gateway_response'] = gateway_response
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error processing payment: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get payment details"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        return jsonify(payment.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/payments/order/<int:order_id>', methods=['GET'])
def get_payments_by_order(order_id):
    """Get all payments for a specific order"""
    try:
        payments = Payment.query.filter_by(order_id=order_id).all()
        return jsonify([payment.to_dict() for payment in payments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payments/user/<int:user_id>', methods=['GET'])
def get_payments_by_user(user_id):
    """Get all payments for a specific user"""
    try:
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
        return jsonify([payment.to_dict() for payment in payments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payments/<int:payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """Process payment refund"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if payment.payment_status != 'completed':
            return jsonify({'error': 'Only completed payments can be refunded'}), 400
        
        # Simulate refund processing
        refund_response = simulate_payment_gateway('refund', payment.amount)
        
        if refund_response['status'] == 'success':
            payment.payment_status = 'refunded'
            payment.updated_at = datetime.datetime.utcnow()
            db.session.commit()
            
            # Update order status
            update_order_status(payment.order_id, 'cancelled')
            
            # Send refund notification
            send_payment_notification(payment.user_id, payment.to_dict(), payment.order_id)
            
            return jsonify({
                'message': 'Refund processed successfully',
                'payment': payment.to_dict(),
                'refund_response': refund_response
            }), 200
        else:
            return jsonify({'error': 'Refund processing failed', 'details': refund_response}), 500
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error processing refund: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/payments', methods=['GET'])
def get_all_payments():
    """Get all payments (admin endpoint)"""
    try:
        status = request.args.get('status')
        
        query = Payment.query
        if status:
            query = query.filter_by(payment_status=status)
        
        payments = query.order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments],
            'count': len(payments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payments/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics"""
    try:
        total_payments = Payment.query.count()
        completed_payments = Payment.query.filter_by(payment_status='completed').count()
        failed_payments = Payment.query.filter_by(payment_status='failed').count()
        total_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(payment_status='completed').scalar() or 0
        
        return jsonify({
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'failed_payments': failed_payments,
            'success_rate': round((completed_payments / total_payments * 100) if total_payments > 0 else 0, 2),
            'total_revenue': float(total_amount)
        }), 200
        
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
    print("="*80, file=sys.stderr)
    print("PAYMENT SERVICE STARTING", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Database: {DB_NAME}", file=sys.stderr)
    print(f"Host:     {DB_HOST}", file=sys.stderr)
    print(f"Port:     5003", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Order Service:        {ORDER_SERVICE_URL}", file=sys.stderr)
    print(f"User Service:         {USER_SERVICE_URL}", file=sys.stderr)
    print(f"Notification Service: {NOTIFICATION_SERVICE_URL}", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!", file=sys.stderr)
        except Exception as e:
            print(f"❌ Database connection failed: {e}", file=sys.stderr)
            print("⚠️  Service will start but may not function properly", file=sys.stderr)
    
    port = int(os.getenv('PORT', 5003))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)