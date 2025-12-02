from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import importlib
import importlib.util
from dotenv import load_dotenv; load_dotenv() 


# ════════════════════════════════════════════════════════════════════════════════
# EMAIL CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════
# Try to load optional email_config module dynamically to avoid static import errors
_EMAIL_CONFIG = None
if importlib.util.find_spec('email_config') is not None:
    try:
        _mod = importlib.import_module('email_config')
        _EMAIL_CONFIG = getattr(_mod, 'EMAIL_CONFIG', None)
    except Exception:
        _EMAIL_CONFIG = None

if _EMAIL_CONFIG:
    SMTP_SERVER = os.getenv('SMTP_SERVER', _EMAIL_CONFIG.get('SMTP_SERVER', 'smtp.gmail.com'))
    SMTP_PORT = int(os.getenv('SMTP_PORT', str(_EMAIL_CONFIG.get('SMTP_PORT', 587))))
    EMAIL_USER = os.getenv('EMAIL_USER', _EMAIL_CONFIG.get('EMAIL_USER', 'your-email@gmail.com'))
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', _EMAIL_CONFIG.get('EMAIL_PASSWORD', ''))
    ENABLE_REAL_EMAIL_SENDING = os.getenv('ENABLE_REAL_EMAIL_SENDING', 'False').lower() == 'true'
    FROM_NAME = os.getenv('FROM_NAME', _EMAIL_CONFIG.get('FROM_NAME', 'ShopEase E-Commerce'))
else:
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER', 'your-email@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    ENABLE_REAL_EMAIL_SENDING = os.getenv('ENABLE_REAL_EMAIL_SENDING', 'False').lower() == 'true'
    FROM_NAME = os.getenv('FROM_NAME', 'ShopEase E-Commerce')
    
print(f"ENABLE_REAL_EMAIL_SENDING status: {ENABLE_REAL_EMAIL_SENDING}")
print(f"EMAIL_USER: {EMAIL_USER}")

app = Flask(__name__)
CORS(app)

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

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://shopease-alb-1528125855.us-east-1.elb.amazonaws.com/api/users')

# ════════════════════════════════════════════════════════════════════════════════
# NOTIFICATION MODEL - Maps to 'notifications' table in notificationdb
# ════════════════════════════════════════════════════════════════════════════════

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')
    delivery_method = db.Column(db.String(50), default='email')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'category': self.category,
            'title': self.title,
            'message': self.message,
            'status': self.status,
            'delivery_method': self.delivery_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def get_user_details(user_id):
    """Fetch user details from user service"""
    try:
        response = requests.get(f'{USER_SERVICE_URL}/{user_id}', timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"⚠️ Failed to get user details for user_id {user_id}: {str(e)}", file=sys.stderr)
        return None

def send_email_notification(recipient_email, subject, message):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{FROM_NAME} <{EMAIL_USER}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        
        if ENABLE_REAL_EMAIL_SENDING and EMAIL_USER != 'your-email@gmail.com':
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_USER, recipient_email, text)
            server.quit()
            
            print(f"✉️  REAL EMAIL SENT to {recipient_email}", file=sys.stderr)
            return True, "Email sent successfully to " + recipient_email
        else:
            # Demo mode
            print("\n" + "="*60, file=sys.stderr)
            print("📧 EMAIL NOTIFICATION (DEMO MODE)", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(f"From: {FROM_NAME} <{EMAIL_USER}>", file=sys.stderr)
            print(f"To: {recipient_email}", file=sys.stderr)
            print(f"Subject: {subject}", file=sys.stderr)
            print("-"*60, file=sys.stderr)
            print("MESSAGE CONTENT:", file=sys.stderr)
            print(message[:500], file=sys.stderr)  # First 500 chars
            print("="*60, file=sys.stderr)
            print("✅ Email simulation completed successfully!", file=sys.stderr)
            print("="*60 + "\n", file=sys.stderr)
            
            return True, f"Email simulated successfully for {recipient_email}"
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}", file=sys.stderr)
        return False, str(e)

def send_sms_notification(phone_number, message):
    """Send SMS notification (simulated)"""
    print(f"📱 SMS to {phone_number}: {message}", file=sys.stderr)
    return True, "SMS sent successfully"

def create_email_template(category, data):
    """Create email template based on notification category"""
    templates = {
        'order_confirmation': {
            'subject': f'Order Confirmation - Order #{data.get("order_id", "N/A")}',
            'body': f'''
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #4CAF50;">Order Confirmation</h2>
                <p>Dear Customer,</p>
                <p>Thank you for your order! Your order has been successfully placed.</p>
                <p><strong>Order Details:</strong></p>
                <ul>
                    <li>Order ID: #{data.get("order_id", "N/A")}</li>
                    <li>Total Amount: ₹{data.get("amount", "0")}</li>
                    <li>Status: {data.get("status", "Confirmed")}</li>
                </ul>
                <p>You will receive another notification once your order is shipped.</p>
                <p>Thank you for shopping with ShopEase!</p>
            </body>
            </html>
            '''
        },
        'payment_confirmation': {
            'subject': f'Payment Confirmation - Order #{data.get("order_id", "N/A")}',
            'body': f'''
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2196F3; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .success {{ background: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 15px 0; }}
                    .details {{ background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Payment Successful!</h1>
                    </div>
                    <div class="content">
                        <div class="success">
                            <strong>✅ Your payment has been successfully processed!</strong>
                        </div>
                        <div class="details">
                            <h3>Payment Details:</h3>
                            <table style="width: 100%;">
                                <tr><td><b>Order ID:</b></td><td>#{data.get("order_id", "N/A")}</td></tr>
                                <tr><td><b>Amount Paid:</b></td><td style="color: #4CAF50;">₹{data.get("amount", "0")}</td></tr>
                                <tr><td><b>Payment Method:</b></td><td>{data.get("payment_method", "N/A").title()}</td></tr>
                                <tr><td><b>Date:</b></td><td>{datetime.datetime.now().strftime('%B %d, %Y')}</td></tr>
                            </table>
                        </div>
                        <p>Your order is now being processed!</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'user_registration': {
            'subject': 'Welcome to ShopEase!',
            'body': f'''
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #4CAF50;">Welcome to ShopEase!</h1>
                    <p>Hi {data.get('username', 'Customer')}!</p>
                    <p>Your account has been successfully created.</p>
                    <p><strong>Account Details:</strong></p>
                    <ul>
                        <li>Username: {data.get('username', 'N/A')}</li>
                        <li>Email: {data.get('email', 'N/A')}</li>
                    </ul>
                    <p>Start shopping now!</p>
                </div>
            </body>
            </html>
            '''
        },
        'general': {
            'subject': data.get('title', 'Notification from ShopEase'),
            'body': f'''
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>{data.get('title', 'Notification')}</h2>
                <p>Dear Customer,</p>
                <p>{data.get('message', 'You have a new notification.')}</p>
                <p>Thank you!</p>
            </body>
            </html>
            '''
        }
    }
    
    return templates.get(category, templates['general'])

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
        'service': 'notification_service',
        'database': db_status,
        'db_name': DB_NAME,
        'db_host': DB_HOST,
        'email_enabled': ENABLE_REAL_EMAIL_SENDING
    }), 200

@app.route('/test-email', methods=['POST'])
def test_email():
    """Test email sending directly"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'subject', 'category']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: email, subject, category'}), 400
        
        template_data = {
            'title': data.get('subject', 'Test Email'),
            'message': data.get('message', 'This is a test email'),
            'username': data.get('username', 'Test User'),
            'email': data.get('email'),
            'order_id': data.get('order_id', '12345'),
            'amount': data.get('amount', '1000'),
            'payment_method': data.get('payment_method', 'card')
        }
        
        template = create_email_template(data['category'], template_data)
        success, error_message = send_email_notification(
            data['email'], 
            template['subject'], 
            template['body']
        )
        
        if success:
            return jsonify({
                'message': 'Test email sent successfully',
                'recipient': data['email'],
                'success': True
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send test email',
                'details': error_message,
                'success': False
            }), 500
            
    except Exception as e:
        print(f"❌ Error in test_email: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    """Create and send a notification"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'type', 'message']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: user_id, type, message'}), 400
        
        # Get user details
        user = get_user_details(data['user_id'])
        
        if not user and data.get('email'):
            user = {
                'id': data['user_id'],
                'email': data['email'],
                'username': data.get('username', 'User')
            }
        elif not user:
            return jsonify({'error': 'User not found and no email provided'}), 404
        
        # Create notification
        notification = Notification(
            user_id=data['user_id'],
            type=data['type'],
            category=data.get('category', 'general'),
            title=data.get('title', ''),
            message=data['message'],
            delivery_method=data.get('delivery_method', 'email')
        )
        
        db.session.add(notification)
        db.session.flush()
        
        # Send notification
        success = False
        error_message = ""
        
        if notification.delivery_method == 'email':
            template = create_email_template(notification.category, data)
            success, error_message = send_email_notification(
                user['email'], 
                template['subject'], 
                template['body']
            )
        elif notification.delivery_method == 'sms':
            success, error_message = send_sms_notification(
                user.get('phone', ''), 
                notification.message
            )
        else:
            success = True
            error_message = "In-app notification created"
        
        # Update status
        notification.status = 'sent' if success else 'failed'
        
        db.session.commit()
        
        response_data = notification.to_dict()
        response_data['delivery_status'] = 'sent' if success else 'failed'
        response_data['delivery_message'] = error_message
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating notification: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get notification details"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        return jsonify(notification.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/notifications/user/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Get all notifications for a user"""
    try:
        notifications = Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_all_notifications():
    """Get all notifications"""
    try:
        status = request.args.get('status')
        category = request.args.get('category')
        
        query = Notification.query
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        
        notifications = query.order_by(Notification.created_at.desc()).all()
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications],
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification statistics"""
    try:
        total = Notification.query.count()
        sent = Notification.query.filter_by(status='sent').count()
        failed = Notification.query.filter_by(status='failed').count()
        
        return jsonify({
            'total_notifications': total,
            'sent_notifications': sent,
            'failed_notifications': failed,
            'success_rate': round((sent / total * 100) if total > 0 else 0, 2)
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
    print("NOTIFICATION SERVICE STARTING", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Database: {DB_NAME}", file=sys.stderr)
    print(f"Host:     {DB_HOST}", file=sys.stderr)
    print(f"Port:     5005", file=sys.stderr)
    print(f"Email:    {'ENABLED' if ENABLE_REAL_EMAIL_SENDING else 'DEMO MODE'}", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"User Service: {USER_SERVICE_URL}", file=sys.stderr)
    print("="*80, file=sys.stderr)
    
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!", file=sys.stderr)
        except Exception as e:
            print(f"❌ Database connection failed: {e}", file=sys.stderr)
            print("⚠️  Service will start but may not function properly", file=sys.stderr)
    
    port = int(os.getenv('PORT', 5005))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)