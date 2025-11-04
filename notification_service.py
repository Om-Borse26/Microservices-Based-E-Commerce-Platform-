from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import email configuration
try:
    from email_config import EMAIL_CONFIG
    # Use configuration from email_config.py
    SMTP_SERVER = os.getenv('SMTP_SERVER', EMAIL_CONFIG['SMTP_SERVER'])
    SMTP_PORT = int(os.getenv('SMTP_PORT', EMAIL_CONFIG['SMTP_PORT']))
    EMAIL_USER = os.getenv('EMAIL_USER', EMAIL_CONFIG['EMAIL_USER'])
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', EMAIL_CONFIG['EMAIL_PASSWORD'])
    ENABLE_REAL_EMAIL_SENDING = os.getenv('ENABLE_REAL_EMAIL_SENDING', str(EMAIL_CONFIG['ENABLE_REAL_EMAIL_SENDING'])).lower() == 'true'
    FROM_NAME = os.getenv('FROM_NAME', EMAIL_CONFIG['FROM_NAME'])
except ImportError:
    # Direct configuration - use your actual Gmail credentials
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER', 'your-email@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    ENABLE_REAL_EMAIL_SENDING = os.getenv('ENABLE_REAL_EMAIL_SENDING', 'False').lower() == 'true'
    FROM_NAME = os.getenv('FROM_NAME', 'ShopEase E-Commerce')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Database via env var with fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:Yog%40101619@localhost/notificationdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuration for other microservices via env
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')

# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Reference to user service
    type = db.Column(db.String(50), nullable=False)  # email, sms, push, in_app
    category = db.Column(db.String(50), nullable=False)  # order_confirmation, payment_confirmation, shipping_update, etc.
    title = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed, read
    delivery_method = db.Column(db.String(50), default='email')  # email, sms, push
    recipient = db.Column(db.String(200))  # email address or phone number
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Additional metadata
    order_id = db.Column(db.Integer)
    payment_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
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
            'recipient': self.recipient,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat(),
            'order_id': self.order_id,
            'payment_id': self.payment_id,
            'retry_count': self.retry_count
        }

# Helper functions
def get_user_details(user_id):
    """Fetch user details from user service"""
    try:
        # Try to get specific user first
        response = requests.get(f'{USER_SERVICE_URL}/users/{user_id}', timeout=5)
        if response.status_code == 200:
            return response.json()
        
        # Fallback: get all users and filter (for backward compatibility)
        response = requests.get(f'{USER_SERVICE_URL}/users', timeout=5)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user['id'] == user_id:
                    return user
        return None
    except requests.RequestException as e:
        print(f"❌ Failed to get user details for user_id {user_id}: {str(e)}")
        return None

def send_email_notification(recipient_email, subject, message):
    """Send email notification"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{FROM_NAME} <{EMAIL_USER}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'html'))
        
        if ENABLE_REAL_EMAIL_SENDING and EMAIL_USER != 'your-email@gmail.com':
            # Real email sending - only if properly configured
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(EMAIL_USER, recipient_email, text)
            server.quit()
            
            print(f"✉️  REAL EMAIL SENT to {recipient_email}")
            print(f"📧 Subject: {subject}")
            return True, "Email sent successfully to " + recipient_email
        else:
            # Demo mode - simulate email sending with detailed output
            print("\n" + "="*60)
            print("📧 EMAIL NOTIFICATION (DEMO MODE)")
            print("="*60)
            print(f"From: {FROM_NAME} <{EMAIL_USER}>")
            print(f"To: {recipient_email}")
            print(f"Subject: {subject}")
            print("-"*60)
            print("MESSAGE CONTENT:")
            print(message)
            print("="*60)
            print("✅ Email simulation completed successfully!")
            if EMAIL_USER == 'your-email@gmail.com':
                print("💡 To send real emails:")
                print("   1. Edit email_config.py with your Gmail credentials")
                print("   2. Set ENABLE_REAL_EMAIL_SENDING = True")
            else:
                print("💡 To send real emails, set ENABLE_REAL_EMAIL_SENDING = True")
            print("="*60 + "\n")
            
            return True, f"Email simulated successfully for {recipient_email}"
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False, str(e)
        return False, str(e)

def send_sms_notification(phone_number, message):
    """Send SMS notification (simulated)"""
    try:
        # In a real application, you would integrate with SMS providers like:
        # - Twilio
        # - AWS SNS
        # - Firebase Cloud Messaging
        # For demo, we'll simulate SMS sending
        
        print(f"📱 SMS to {phone_number}: {message}")
        return True, "SMS sent successfully"
    except Exception as e:
        return False, str(e)

def create_email_template(category, data):
    """Create email template based on notification category"""
    templates = {
        'order_confirmation': {
            'subject': f'Order Confirmation - Order #{data.get("order_id", "N/A")}',
            'body': f'''
            <html>
            <body>
                <h2>Order Confirmation</h2>
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
                    .footer {{ padding: 20px; text-align: center; color: #666; }}
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
                        <h2>Payment Confirmation</h2>
                        <p>Dear Customer,</p>
                        <p>Thank you for your payment. Your transaction has been completed successfully.</p>
                        
                        <div class="details">
                            <h3>Payment Details:</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px; font-weight: bold;">Payment ID:</td>
                                    <td style="padding: 8px;">{data.get("payment_id", "N/A")}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px; font-weight: bold;">Order ID:</td>
                                    <td style="padding: 8px;">#{data.get("order_id", "N/A")}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px; font-weight: bold;">Amount Paid:</td>
                                    <td style="padding: 8px; color: #4CAF50; font-weight: bold;">₹{data.get("amount", "0")}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px; font-weight: bold;">Payment Status:</td>
                                    <td style="padding: 8px; color: #4CAF50;">{data.get("payment_status", "Completed").title()}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 8px; font-weight: bold;">Payment Method:</td>
                                    <td style="padding: 8px;">{data.get("payment_method", "N/A").title()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Transaction Date:</td>
                                    <td style="padding: 8px;">{datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p>Your order is now being processed and will be shipped soon. You will receive another notification with tracking details once your order is dispatched.</p>
                        
                        <p>If you have any questions about your payment or order, please contact our support team at sparxvenom69@gmail.com</p>
                    </div>
                    <div class="footer">
                        <p>Thank you for your business!</p>
                        <p>Best regards,<br>The ShopEase Team</p>
                        <p><small>This is an automated message. Please do not reply to this email.</small></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'shipping_update': {
            'subject': f'Shipping Update - Order #{data.get("order_id", "N/A")}',
            'body': f'''
            <html>
            <body>
                <h2>Shipping Update</h2>
                <p>Dear Customer,</p>
                <p>Your order has been shipped!</p>
                <p><strong>Shipping Details:</strong></p>
                <ul>
                    <li>Order ID: #{data.get("order_id", "N/A")}</li>
                    <li>Tracking Number: {data.get("tracking_number", "N/A")}</li>
                    <li>Estimated Delivery: {data.get("estimated_delivery", "3-5 business days")}</li>
                </ul>
                <p>You can track your package using the tracking number provided.</p>
            </body>
            </html>
            '''
        },
        'welcome': {
            'subject': 'Welcome to ShopEase! Your Account is Ready',
            'body': f'''
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; }}
                    .button {{ background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to ShopEase!</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {data.get('username', 'Valued Customer')}!</h2>
                        <p>Thank you for registering with ShopEase. Your account has been successfully created!</p>
                        <p><strong>Your Account Details:</strong></p>
                        <ul>
                            <li>Email: {data.get('email', 'N/A')}</li>
                            <li>Registration Date: {datetime.datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                        <p>You can now start shopping and enjoy our wide range of products with exclusive deals and offers.</p>
                        <p style="text-align: center;">
                            <a href="http://localhost:3000" class="button">Start Shopping</a>
                        </p>
                        <p>If you have any questions or need assistance, feel free to contact our support team.</p>
                    </div>
                    <div class="footer">
                        <p>Thank you for choosing ShopEase!</p>
                        <p>Best regards,<br>The ShopEase Team</p>
                        <p><small>This is an automated message. Please do not reply to this email.</small></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'user_registration': {
            'subject': 'Welcome to ShopEase! Your Account is Ready',
            'body': f'''
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; }}
                    .button {{ background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to ShopEase!</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {data.get('username', 'Valued Customer')}!</h2>
                        <p>Thank you for registering with ShopEase. Your account has been successfully created!</p>
                        <p><strong>Your Account Details:</strong></p>
                        <ul>
                            <li>Username: {data.get('username', 'N/A')}</li>
                            <li>Email: {data.get('email', 'N/A')}</li>
                            <li>Registration Date: {datetime.datetime.now().strftime('%B %d, %Y')}</li>
                        </ul>
                        <p>You can now start shopping and enjoy our wide range of products with exclusive deals and offers.</p>
                        <p style="text-align: center;">
                            <a href="http://localhost:3000" class="button">Start Shopping</a>
                        </p>
                        <p>If you have any questions or need assistance, feel free to contact our support team at sparxvenom69@gmail.com</p>
                    </div>
                    <div class="footer">
                        <p>Thank you for choosing ShopEase!</p>
                        <p>Best regards,<br>The ShopEase Team</p>
                        <p><small>This is an automated message. Please do not reply to this email.</small></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'general': {
            'subject': data.get('title', 'Notification from ShopEase'),
            'body': f'''
            <html>
            <body>
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

# Routes

@app.route('/test-email', methods=['POST'])
def test_email():
    """Test email sending directly without user lookup"""
    try:
        data = request.get_json()
        
        # Required fields for direct email test
        required_fields = ['email', 'subject', 'category']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: email, subject, category'}), 400
        
        # Create email template
        template_data = {
            'title': data.get('subject', 'Test Email'),
            'message': data.get('message', 'This is a test email'),
            'username': data.get('username', 'Test User'),
            'email': data.get('email'),
            'first_name': data.get('first_name', 'Test'),
            'last_name': data.get('last_name', 'User'),
            'order_id': data.get('order_id', '12345'),
            'payment_id': data.get('payment_id', 'PAY_TEST123'),
            'amount': data.get('amount', '1000'),
            'payment_status': data.get('payment_status', 'completed'),
            'payment_method': data.get('payment_method', 'card'),
            'transaction_id': data.get('transaction_id', 'TXN_TEST456')
        }
        
        template = create_email_template(data['category'], template_data)
        
        # Send email directly
        success, error_message = send_email_notification(
            data['email'], 
            template['subject'], 
            template['body']
        )
        
        if success:
            return jsonify({
                'message': 'Test email sent successfully',
                'recipient': data['email'],
                'subject': template['subject'],
                'category': data['category'],
                'success': True
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send test email',
                'details': error_message,
                'success': False
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'service': 'notification_service'}), 200

@app.route('/notifications', methods=['POST'])
def create_notification():
    """Create and send a new notification"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['user_id', 'type', 'message']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: user_id, type, message'}), 400
        
        # Get user details - but allow fallback if user service is unavailable
        user = get_user_details(data['user_id'])
        
        # If we can't get user details but email is provided directly, use that
        if not user and data.get('email'):
            user = {
                'id': data['user_id'],
                'email': data['email'],
                'username': data.get('username', 'User'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', '')
            }
        elif not user:
            return jsonify({'error': 'User not found and no email provided'}), 404
        
        # Create notification record
        notification = Notification(
            user_id=data['user_id'],
            type=data['type'],
            category=data.get('category', 'general'),
            title=data.get('title', ''),
            message=data['message'],
            delivery_method=data.get('delivery_method', 'email'),
            recipient=user['email'],  # Default to email
            order_id=data.get('order_id'),
            payment_id=data.get('payment_id')
        )
        
        db.session.add(notification)
        db.session.flush()  # Get the notification ID
        
        # Send notification based on delivery method
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
            # Would need phone number from user profile
            success, error_message = send_sms_notification(
                user.get('phone', ''), 
                notification.message
            )
        else:
            # For in_app notifications, just mark as sent
            success = True
            error_message = "In-app notification created"
        
        # Update notification status
        if success:
            notification.status = 'sent'
            notification.sent_at = datetime.datetime.utcnow()
        else:
            notification.status = 'failed'
            notification.error_message = error_message
        
        db.session.commit()
        
        response_data = notification.to_dict()
        response_data['delivery_status'] = 'sent' if success else 'failed'
        response_data['delivery_message'] = error_message
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get notification details"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        return jsonify(notification.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/notifications/user/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Get all notifications for a specific user"""
    try:
        notifications = Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        notification.read_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify(notification.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/notifications', methods=['GET'])
def get_all_notifications():
    """Get all notifications (admin endpoint)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        category = request.args.get('category')
        
        query = Notification.query
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': notifications.total,
                'pages': notifications.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/retry/<int:notification_id>', methods=['POST'])
def retry_notification(notification_id):
    """Retry failed notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        if notification.status != 'failed':
            return jsonify({'error': 'Only failed notifications can be retried'}), 400
        
        if notification.retry_count >= 3:
            return jsonify({'error': 'Maximum retry attempts reached'}), 400
        
        # Get user details
        user = get_user_details(notification.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Retry sending
        success = False
        error_message = ""
        
        if notification.delivery_method == 'email':
            template = create_email_template(notification.category, {
                'title': notification.title,
                'message': notification.message,
                'order_id': notification.order_id,
                'payment_id': notification.payment_id
            })
            success, error_message = send_email_notification(
                user['email'], 
                template['subject'], 
                template['body']
            )
        
        # Update notification
        notification.retry_count += 1
        if success:
            notification.status = 'sent'
            notification.sent_at = datetime.datetime.utcnow()
            notification.error_message = None
        else:
            notification.error_message = error_message
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notification retry completed',
            'notification': notification.to_dict(),
            'success': success
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification statistics"""
    try:
        total_notifications = Notification.query.count()
        sent_notifications = Notification.query.filter_by(status='sent').count()
        failed_notifications = Notification.query.filter_by(status='failed').count()
        pending_notifications = Notification.query.filter_by(status='pending').count()
        
        # Stats by category
        categories = db.session.query(
            Notification.category, 
            db.func.count(Notification.id)
        ).group_by(Notification.category).all()
        
        return jsonify({
            'total_notifications': total_notifications,
            'sent_notifications': sent_notifications,
            'failed_notifications': failed_notifications,
            'pending_notifications': pending_notifications,
            'success_rate': round((sent_notifications / total_notifications * 100) if total_notifications > 0 else 0, 2),
            'categories': dict(categories)
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
    port = int(os.getenv('PORT', 5005))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
