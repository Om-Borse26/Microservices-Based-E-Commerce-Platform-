from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import uuid
import random
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Database via env var with fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:Yog%40101619@localhost/paymentdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuration for other microservices via env
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:5002')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:5005')
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')

# Payment Model
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(100), unique=True, nullable=False)  # Unique payment identifier
    order_id = db.Column(db.Integer, nullable=False)  # Reference to order service
    user_id = db.Column(db.Integer, nullable=False)   # Reference to user service
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    payment_method = db.Column(db.String(50), nullable=False)  # card, upi, netbanking, wallet
    payment_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed, refunded
    transaction_id = db.Column(db.String(100))  # External payment gateway transaction ID
    gateway_response = db.Column(db.Text)  # Store gateway response
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Card details (for demonstration - in real world, never store raw card data)
    card_last_four = db.Column(db.String(4))
    card_brand = db.Column(db.String(20))
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'card_last_four': self.card_last_four,
            'card_brand': self.card_brand
        }

# Helper functions
def generate_payment_id():
    """Generate unique payment ID"""
    return f"PAY_{uuid.uuid4().hex[:12].upper()}"

def generate_transaction_id():
    """Generate mock transaction ID"""
    return f"TXN_{uuid.uuid4().hex[:16].upper()}"

def simulate_payment_gateway(payment_method, amount, card_details=None):
    """Simulate payment gateway processing"""
    # Simulate processing time
    import time
    time.sleep(1)
    
    # Simulate random success/failure (90% success rate)
    success_rate = 0.9
    is_successful = random.random() < success_rate
    
    if is_successful:
        return {
            'status': 'success',
            'transaction_id': generate_transaction_id(),
            'message': 'Payment processed successfully',
            'gateway_fee': round(amount * 0.02, 2)  # 2% gateway fee
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
            json={'status': status}
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

def send_payment_notification(user_id, payment_data, order_id):
    """Send payment notification via notification service"""
    try:
        # First, try to get user email from user service
        user_email = None
        user_name = "Customer"
        
        try:
            user_response = requests.get(f'{USER_SERVICE_URL}/users/{user_id}', timeout=5)
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_email = user_data.get('email')
                user_name = user_data.get('first_name') or user_data.get('username', 'Customer')
        except requests.RequestException:
            print(f"⚠️  Could not get user details from user service for user_id {user_id}")
        
        notification_data = {
            'user_id': user_id,
            'type': 'email',
            'category': 'payment_confirmation',
            'title': f'Payment Confirmation - Order #{order_id}',
            'message': f"Payment of ₹{payment_data['amount']} for Order #{order_id} has been {payment_data['payment_status']}",
            'payment_id': payment_data['payment_id'],
            'order_id': order_id,
            'amount': payment_data['amount'],
            'payment_status': payment_data['payment_status'],
            'payment_method': payment_data['payment_method'],
            'transaction_id': payment_data.get('transaction_id', 'N/A'),
            'username': user_name
        }
        
        # Include email if we got it from user service
        if user_email:
            notification_data['email'] = user_email
        
        response = requests.post(
            f'{NOTIFICATION_SERVICE_URL}/notifications',
            headers={'Content-Type': 'application/json'},
            json=notification_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Payment notification sent successfully for payment {payment_data['payment_id']}")
            return True
        else:
            print(f"⚠️  Payment notification failed with status {response.status_code}")
            print(f"⚠️  Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Payment notification failed: {str(e)}")
        return False

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'service': 'payment_service'}), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    """Process a new payment"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['order_id', 'user_id', 'amount', 'payment_method']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: order_id, user_id, amount, payment_method'}), 400
        
        # Create payment record
        payment = Payment(
            payment_id=generate_payment_id(),
            order_id=data['order_id'],
            user_id=data['user_id'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            payment_status='processing'
        )
        
        # Handle card details if provided
        if data['payment_method'] == 'card' and 'card_details' in data:
            card_details = data['card_details']
            payment.card_last_four = card_details.get('number', '')[-4:] if card_details.get('number') else None
            payment.card_brand = card_details.get('brand', 'Unknown')
        
        db.session.add(payment)
        db.session.flush()  # Get the payment ID
        
        # Process payment through gateway
        gateway_response = simulate_payment_gateway(
            data['payment_method'], 
            data['amount'], 
            data.get('card_details')
        )
        
        # Update payment based on gateway response
        payment.gateway_response = str(gateway_response)
        payment.transaction_id = gateway_response.get('transaction_id')
        
        if gateway_response['status'] == 'success':
            payment.payment_status = 'completed'
            order_status = 'confirmed'
        else:
            payment.payment_status = 'failed'
            order_status = 'pending'
        
        payment.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        # Update order status
        update_order_status(payment.order_id, order_status)
        
        # Send notification
        send_payment_notification(payment.user_id, payment.to_dict(), payment.order_id)
        
        response_data = payment.to_dict()
        response_data['gateway_response'] = gateway_response
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get payment details"""
    try:
        payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
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

@app.route('/payments/<payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """Process payment refund"""
    try:
        payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
        
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
        return jsonify({'error': str(e)}), 500

@app.route('/payments', methods=['GET'])
def get_all_payments():
    """Get all payments (admin endpoint)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Payment.query
        if status:
            query = query.filter_by(payment_status=status)
        
        payments = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': payments.total,
                'pages': payments.pages
            }
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
            'total_revenue': total_amount
        }), 200
        
    except Exception as e:
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
    port = int(os.getenv('PORT', 5003))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
