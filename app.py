from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
import datetime
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import security and configuration modules
from security import (
    login_required, role_required, validate_input, validate_file,
    sanitize_filename, add_security_headers, rate_limit_check
)
from config import get_config

# Database initialization
def init_db():
    conn = sqlite3.connect('land_registry.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create land_records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_number TEXT UNIQUE NOT NULL,
            khatian_number TEXT,
            dag_number TEXT,
            owner_id INTEGER,
            area REAL NOT NULL,
            market_value INTEGER NOT NULL,
            land_type TEXT NOT NULL,
            division TEXT NOT NULL,
            district TEXT NOT NULL,
            upazila TEXT NOT NULL,
            mouza TEXT,
            address TEXT NOT NULL,
            description TEXT,
            location TEXT,
            status TEXT DEFAULT 'registered',
            hash_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    
    # Create blockchain table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_hash TEXT NOT NULL,
            previous_hash TEXT,
            data TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            seller_id INTEGER,
            buyer_email TEXT NOT NULL,
            buyer_phone TEXT,
            sale_price INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            transfer_date DATE NOT NULL,
            registration_fee INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES land_records (id),
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            document_type TEXT NOT NULL,
            document_title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_by INTEGER,
            verification_status TEXT DEFAULT 'pending',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES land_records (id),
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''')
    
    # Create admin_notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def create_app(config_class=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        config_class = get_config(config_name)
    
    app.config.from_object(config_class)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Custom Jinja2 filter to extract numeric area values
    @app.template_filter('extract_area')
    def extract_area_filter(area_value):
        """Extract numeric value from area field (handles both numeric and string values)"""
        import re
        if isinstance(area_value, (int, float)):
            return float(area_value)
        elif isinstance(area_value, str):
            # Extract first numeric value from string
            match = re.search(r'\d+(?:\.\d+)?', area_value)
            return float(match.group()) if match else 0.0
        else:
            return 0.0
    
    # Setup logging
    if not app.debug:
        logging.basicConfig(
            filename=app.config.get('LOG_FILE', 'app.log'),
            level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
            format='%(asctime)s %(levelname)s: %(message)s'
        )
    
    # Add security headers to all responses
    @app.after_request
    def after_request(response):
        return add_security_headers(response)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            conn.close()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.datetime.now().isoformat(),
                'database': 'connected',
                'user_count': user_count,
                'version': '1.0.0'
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.datetime.now().isoformat(),
                'error': str(e)
            }), 503
    
    return app

# Create app instance
app = create_app()

# Database tables are now created in the init_db() function above

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('land_registry.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_hash(data):
    return hashlib.sha256(str(data).encode()).hexdigest()

def create_block(data, previous_hash=''):
    timestamp = datetime.datetime.now().isoformat()
    block_data = {
        'data': data,
        'timestamp': timestamp,
        'previous_hash': previous_hash
    }
    block_hash = calculate_hash(block_data)
    return block_hash, block_data

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Rate limiting check
        if not rate_limit_check(f"{request.remote_addr}_register", 3, 3600):  # 3 registrations per hour
            flash('Too many registration attempts. Please try again later.', 'error')
            return render_template('register.html'), 429
        
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Input validation
        is_valid, _ = validate_input(full_name, 'text')
        if not is_valid or len(full_name) < 2:
            flash('Name must be at least 2 characters long and contain only letters and spaces.', 'error')
            return render_template('register.html')
        
        is_valid, _ = validate_input(email, 'email')
        if not is_valid:
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')
        
        if phone:
            is_valid, _ = validate_input(phone, 'phone')
            if not is_valid:
                flash('Please enter a valid phone number.', 'error')
                return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if role not in ['admin', 'owner', 'buyer']:
            flash('Invalid role selected', 'error')
            return render_template('register.html')
        
        try:
            conn = get_db_connection()
            
            # Check if user already exists
            existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                flash('Email already registered', 'error')
                return render_template('register.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (?, ?, ?, ?, ?)',
                (email, password_hash, role, full_name, phone)
            )
            conn.commit()
            
            # Log successful registration
            app.logger.info(f'New user registered: {email} with role: {role}')
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError as e:
            app.logger.error(f'Registration integrity error: {str(e)}')
            flash('Registration failed. Please try again.', 'error')
        except Exception as e:
            app.logger.error(f'Registration error: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Rate limiting check
        if not rate_limit_check(f"{request.remote_addr}_login", 5, 300):  # 5 attempts per 5 minutes
            flash('Too many login attempts. Please try again later.', 'error')
            return render_template('login.html'), 429
        
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        is_valid, _ = validate_input(email, 'email')
        if not is_valid:
            flash('Please enter a valid email address.', 'error')
            return render_template('login.html')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('login.html')
        
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                session['user_name'] = user['full_name']
                session['login_time'] = datetime.datetime.now().isoformat()
                flash('Login successful!', 'success')
                
                # Log successful login
                app.logger.info(f'Successful login for user: {email}')
                
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
                app.logger.warning(f'Failed login attempt for email: {email}')
        
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_role = session.get('user_role')
    user_id = session.get('user_id')
    
    # Check session timeout
    login_time = session.get('login_time')
    if login_time:
        login_datetime = datetime.datetime.fromisoformat(login_time)
        session_timeout = app.config.get('SESSION_TIMEOUT', 7200)  # 2 hours default
        if (datetime.datetime.now() - login_datetime).total_seconds() > session_timeout:
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if user_role == 'admin':
        # Admin dashboard - pending transactions and system overview
        pending_transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.address, 
                      u1.full_name as from_user, u2.full_name as to_user
               FROM transactions t
               JOIN land_records l ON t.property_id = l.id
               LEFT JOIN users u1 ON t.seller_id = u1.id
               LEFT JOIN users u2 ON u2.email = t.buyer_email
               WHERE t.status = 'pending'
               ORDER BY t.created_at DESC'''
        ).fetchall()
        
        total_lands = conn.execute('SELECT COUNT(*) as count FROM land_records').fetchone()['count']
        total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        total_transactions = conn.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
        
        conn.close()
        return render_template('admin_dashboard.html', 
                             pending_transactions=pending_transactions,
                             total_lands=total_lands,
                             total_users=total_users,
                             total_transactions=total_transactions)
    
    elif user_role == 'owner':
        # Owner dashboard - their properties and transactions
        properties = conn.execute(
            'SELECT * FROM land_records WHERE owner_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        
        transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.address
               FROM transactions t
               JOIN land_records l ON t.property_id = l.id
               WHERE t.seller_id = ?
               ORDER BY t.created_at DESC LIMIT 10''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        return render_template('owner_dashboard.html', 
                             properties=properties,
                             transactions=transactions)
    
    else:  # buyer
        # Buyer dashboard - available properties and their transactions
        # Only show properties that don't have pending/completed transactions
        available_properties = conn.execute(
            '''SELECT l.*, u.full_name as owner_name
               FROM land_records l
               JOIN users u ON l.owner_id = u.id
               WHERE l.id NOT IN (
                   SELECT DISTINCT property_id 
                   FROM transactions 
                   WHERE status IN ('pending', 'approved', 'completed')
               )
               AND u.role = 'owner'
               ORDER BY l.created_at DESC'''
        ).fetchall()
        
        my_purchases = conn.execute(
            '''SELECT l.*, t.status as transaction_status
               FROM land_records l
               JOIN transactions t ON l.id = t.property_id
               WHERE t.buyer_email = (SELECT email FROM users WHERE id = ?)
               ORDER BY t.created_at DESC''',
            (user_id,)
        ).fetchall()
        
        pending_transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.address
               FROM transactions t
               JOIN land_records l ON t.property_id = l.id
               WHERE t.buyer_email = (SELECT email FROM users WHERE id = ?) AND t.status = 'pending'
               ORDER BY t.created_at DESC''',
            (user_id,)
        ).fetchall()
        
        transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.address
               FROM transactions t
               JOIN land_records l ON t.property_id = l.id
               WHERE t.buyer_email = (SELECT email FROM users WHERE id = ?)
               ORDER BY t.created_at DESC LIMIT 10''',
            (user_id,)
        ).fetchall()
        
        conn.close()
        return render_template('buyer_dashboard.html', 
                             available_properties=available_properties,
                             my_purchases=my_purchases,
                             pending_transactions=pending_transactions,
                             saved_properties=[],  # Placeholder for saved properties
                             transactions=transactions)

@app.route('/register_land', methods=['GET', 'POST'])
@login_required
def register_land():
    if request.method == 'POST':
        # Rate limiting check
        if not rate_limit_check(f"{request.remote_addr}_register_land", 5, 3600):  # 5 registrations per hour
            flash('Too many registration attempts. Please try again later.', 'error')
            return render_template('register_land.html'), 429
        
        # Get and validate form data
        plot_number = request.form.get('plot_number', '').strip()
        khatian_number = request.form.get('khatian_number', '').strip()
        dag_number = request.form.get('dag_number', '').strip()
        land_type = request.form.get('land_type', '').strip()
        area_str = request.form.get('area', '').strip()
        market_value_str = request.form.get('market_value', '').strip()
        division = request.form.get('division', '').strip()
        district = request.form.get('district', '').strip()
        upazila = request.form.get('upazila', '').strip()
        mouza = request.form.get('mouza', '').strip()
        address = request.form.get('address', '').strip()
        description = request.form.get('description', '').strip()
        
        # Input validation
        is_valid, _ = validate_input(plot_number, 'plot_number')
        if not is_valid:
            flash('Please enter a valid plot number.', 'error')
            return render_template('register_land.html')
        
        is_valid, _ = validate_input(area_str, 'numeric')
        if not is_valid or float(area_str) <= 0:
            flash('Please enter a valid area (positive number).', 'error')
            return render_template('register_land.html')
        
        is_valid, _ = validate_input(market_value_str, 'numeric')
        if not is_valid or int(market_value_str) <= 0:
            flash('Please enter a valid market value (positive number).', 'error')
            return render_template('register_land.html')
        
        if not all([plot_number, land_type, division, district, upazila, address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('register_land.html')
        
        try:
            area = float(area_str)
            market_value = int(market_value_str)
        except ValueError:
            flash('Invalid numeric values for area or market value.', 'error')
            return render_template('register_land.html')
        
        # Create property data for blockchain
        property_data = {
            'plot_number': plot_number,
            'khatian_number': khatian_number,
            'dag_number': dag_number,
            'land_type': land_type,
            'area': area,
            'market_value': market_value,
            'location': {
                'division': division,
                'district': district,
                'upazila': upazila,
                'mouza': mouza,
                'address': address
            },
            'description': description,
            'owner_id': session['user_id'],
            'registration_date': datetime.datetime.now().isoformat()
        }
        
        # Calculate hash for blockchain
        property_hash = calculate_hash(json.dumps(property_data, sort_keys=True))
        
        conn = get_db_connection()
        
        try:
            # Check if plot number already exists
            existing = conn.execute(
                'SELECT id FROM land_records WHERE plot_number = ?',
                (plot_number,)
            ).fetchone()
            
            if existing:
                flash('Plot number already exists in the system!', 'error')
                return render_template('register_land.html')
            
            # Create location string
            location = f"{address}, {upazila}, {district}, {division}"
            
            # Insert land record
            cursor = conn.execute('''
                INSERT INTO land_records 
                (plot_number, khatian_number, dag_number, land_type, area, market_value,
                 division, district, upazila, mouza, address, description, location, owner_id, status, hash_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plot_number, khatian_number, dag_number, land_type, area, market_value,
                  division, district, upazila, mouza, address, description, location,
                  session['user_id'], 'registered', property_hash))
            
            property_id = cursor.lastrowid
            
            # Get previous block hash
            prev_block = conn.execute(
                'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
            ).fetchone()
            prev_hash = prev_block['block_hash'] if prev_block else '0'
            
            # Create blockchain entry
            block_data = {
                'type': 'land_registration',
                'property_id': property_id,
                'property_data': property_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            block_hash = calculate_hash(prev_hash + json.dumps(block_data, sort_keys=True))
            
            conn.execute('''
                INSERT INTO blockchain (block_hash, previous_hash, data)
                VALUES (?, ?, ?)
            ''', (block_hash, prev_hash, json.dumps(block_data)))
            
            # Create transaction record
            conn.execute('''
                INSERT INTO transactions 
                (property_id, seller_id, buyer_email, payment_method, sale_price, transfer_date, registration_fee, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (property_id, None, session.get('email', ''), 'cash', 0, datetime.datetime.now().date(), 0, 'completed'))
            
            conn.commit()
            flash('Land property registered successfully on the blockchain!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error registering property: {str(e)}', 'error')
            return render_template('register_land.html')
        finally:
            conn.close()
    
    return render_template('register_land.html')

@app.route('/transfer_property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def transfer_property(property_id):
    conn = get_db_connection()
    
    # Get property details and verify ownership
    property_data = conn.execute('''
        SELECT * FROM land_records WHERE id = ? AND owner_id = ?
    ''', (property_id, session['user_id'])).fetchone()
    
    if not property_data:
        flash('Property not found or you do not have permission to transfer it.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Rate limiting check
        if not rate_limit_check(f"{request.remote_addr}_transfer", 3, 3600):  # 3 transfers per hour
            flash('Too many transfer attempts. Please try again later.', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat()), 429
        
        # Get and validate form data
        buyer_email = request.form.get('buyer_email', '').strip().lower()
        buyer_phone = request.form.get('buyer_phone', '').strip()
        sale_price_str = request.form.get('sale_price', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        transfer_date = request.form.get('transfer_date', '').strip()
        registration_fee_str = request.form.get('registration_fee', '5000').strip()
        notes = request.form.get('notes', '').strip()
        
        # Input validation
        is_valid, _ = validate_input(buyer_email, 'email')
        if not is_valid:
            flash('Please enter a valid buyer email address.', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        if buyer_phone:
            is_valid, _ = validate_input(buyer_phone, 'phone')
            if not is_valid:
                flash('Please enter a valid phone number.', 'error')
                return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        is_valid, _ = validate_input(sale_price_str, 'numeric')
        if not is_valid or int(sale_price_str) <= 0:
            flash('Please enter a valid sale price (positive number).', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        is_valid, _ = validate_input(registration_fee_str, 'numeric')
        if not is_valid or int(registration_fee_str) < 0:
            flash('Please enter a valid registration fee (non-negative number).', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        if not all([buyer_email, payment_method, transfer_date]):
            flash('Please fill in all required fields.', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        try:
            sale_price = int(sale_price_str)
            registration_fee = int(registration_fee_str)
        except ValueError:
            flash('Invalid numeric values for price or fee.', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        
        try:
            # Find buyer by email
            buyer = conn.execute(
                'SELECT * FROM users WHERE email = ? AND role = ?',
                (buyer_email, 'buyer')
            ).fetchone()
            
            if not buyer:
                flash('Buyer not found in the system. Please ensure the buyer is registered.', 'error')
                return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
            
            # Create smart contract data
            contract_data = {
                'type': 'property_transfer',
                'property_id': property_id,
                'seller_id': session['user_id'],
                'buyer_id': buyer['id'],
                'sale_price': sale_price,
                'payment_method': payment_method,
                'transfer_date': transfer_date,
                'registration_fee': registration_fee,
                'notes': notes,
                'contract_terms': {
                    'automatic_transfer': True,
                    'government_approval_required': True,
                    'payment_escrow': True,
                    'digital_certificates': True
                },
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # Get previous block hash
            prev_block = conn.execute(
                'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
            ).fetchone()
            prev_hash = prev_block['block_hash'] if prev_block else '0'
            
            # Create blockchain entry for smart contract
            block_hash = calculate_hash(prev_hash + json.dumps(contract_data, sort_keys=True))
            
            conn.execute('''
                INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
                VALUES (?, ?, ?, ?)
            ''', (block_hash, prev_hash, json.dumps(contract_data), 'smart_contract'))
            
            # Create transaction record
            cursor = conn.execute('''
                INSERT INTO transactions 
                (property_id, seller_id, buyer_email, payment_method, sale_price, transfer_date, registration_fee, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (property_id, session['user_id'], buyer['email'], payment_method, sale_price, transfer_date, registration_fee, 'pending'))
            
            transaction_id = cursor.lastrowid
            
            # Update property status to pending transfer
            conn.execute('''
                UPDATE land_records SET status = ? WHERE id = ?
            ''', ('pending_transfer', property_id))
            
            conn.commit()
            
            flash(f'Property transfer initiated successfully! Smart contract created and pending approval. Transaction ID: {transaction_id}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error initiating transfer: {str(e)}', 'error')
            return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())
        finally:
            conn.close()
    
    conn.close()
    return render_template('transfer_property.html', property=property_data, today=datetime.date.today().isoformat())

@app.route('/approve_transaction/<int:transaction_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_transaction(transaction_id):
    # Rate limiting check
    if not rate_limit_check(f"{request.remote_addr}_admin_action", 20, 3600):  # 20 admin actions per hour
        return jsonify({'success': False, 'message': 'Too many admin actions. Please try again later.'}), 429
    
    print(f"Approving transaction {transaction_id}")
    conn = get_db_connection()
    
    try:
        # Get transaction details
        transaction = conn.execute('''
            SELECT t.*, l.plot_number, l.owner_id
            FROM transactions t
            JOIN land_records l ON t.property_id = l.id
            WHERE t.id = ?
        ''', (transaction_id,)).fetchone()
        
        print(f"Transaction details: {transaction}")
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'})
        
        if transaction['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Transaction is not pending'})
        
        # Update transaction status
        print(f"Updating transaction status to approved for ID {transaction_id}")
        conn.execute('''
            UPDATE transactions SET status = ?
            WHERE id = ?
        ''', ('approved', transaction_id))
        
        # Transfer ownership for all approved transactions
        print(f"Transferring ownership to {transaction['buyer_email']} for property {transaction['property_id']}")
        conn.execute('''
            UPDATE land_records SET owner_id = (SELECT id FROM users WHERE email = ?), status = ?
            WHERE id = ?
        ''', (transaction['buyer_email'], 'active', transaction['property_id']))
        
        # Create blockchain entry for ownership transfer
        transfer_data = {
            'type': 'ownership_transfer',
            'transaction_id': transaction_id,
            'property_id': transaction['property_id'],
            'previous_owner': transaction['seller_id'],
            'new_owner': transaction['buyer_email'],
            'sale_price': transaction['sale_price'],
            'approved_by': session['user_id'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        print(f"Created transfer_data: {transfer_data}")
        
        # Get previous block hash
        prev_block = conn.execute(
            'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
        ).fetchone()
        prev_hash = prev_block['block_hash'] if prev_block else '0'
        print(f"Previous block hash: {prev_hash}")
        
        block_hash = calculate_hash(prev_hash + json.dumps(transfer_data, sort_keys=True))
        print(f"New block hash: {block_hash}")
        
        conn.execute('''
            INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
            VALUES (?, ?, ?, ?)
        ''', (block_hash, prev_hash, json.dumps(transfer_data), 'ownership_transfer'))
        
        conn.commit()
        print("Transaction committed successfully")
        return jsonify({'success': True, 'message': 'Transaction approved successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error approving transaction: {str(e)}'})
    finally:
        conn.close()

@app.route('/reject_transaction/<int:transaction_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_transaction(transaction_id):
    # Rate limiting check
    if not rate_limit_check(f"{request.remote_addr}_admin_action", 20, 3600):  # 20 admin actions per hour
        return jsonify({'success': False, 'message': 'Too many admin actions. Please try again later.'}), 429
    
    conn = get_db_connection()
    
    try:
        # Get transaction details
        transaction = conn.execute('''
            SELECT t.*, l.id as property_id
            FROM transactions t
            JOIN land_records l ON t.property_id = l.id
            WHERE t.id = ?
        ''', (transaction_id,)).fetchone()
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'})
        
        if transaction['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Transaction is not pending'})
        
        # Update transaction status
        conn.execute('''
            UPDATE transactions SET status = ?
            WHERE id = ?
        ''', ('rejected', transaction_id))
        
        # Reset property status for all rejected transactions
        conn.execute('''
            UPDATE land_records SET status = ? WHERE id = ?
        ''', ('active', transaction['property_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Transaction rejected successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error rejecting transaction: {str(e)}'})
    finally:
        conn.close()

@app.route('/upload_documents/<int:property_id>', methods=['GET', 'POST'])
@login_required
def upload_documents(property_id):
    conn = get_db_connection()
    
    # Get property details and verify ownership
    property_data = conn.execute('''
        SELECT * FROM land_records WHERE id = ? AND owner_id = ?
    ''', (property_id, session['user_id'])).fetchone()
    
    if not property_data:
        flash('Property not found or you do not have permission to upload documents.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get existing documents
    documents = conn.execute('''
        SELECT * FROM documents WHERE property_id = ? ORDER BY uploaded_at DESC
    ''', (property_id,)).fetchall()
    
    if request.method == 'POST':
        # Rate limiting check
        if not rate_limit_check(f"{request.remote_addr}_upload", 10, 3600):  # 10 uploads per hour
            flash('Too many upload attempts. Please try again later.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents), 429
        
        # Get form data with validation
        document_type = request.form.get('document_type', '').strip()
        document_title = request.form.get('document_title', '').strip()
        description = request.form.get('description', '').strip()
        document_date = request.form.get('document_date')
        issuing_authority = request.form.get('issuing_authority', '').strip()
        auto_verify = 'auto_verify' in request.form
        blockchain_store = 'blockchain_store' in request.form
        notify_admin = 'notify_admin' in request.form
        
        # Input validation
        is_valid, _ = validate_input(document_title, 'text')
        if not is_valid or len(document_title) < 3:
            flash('Document title must be at least 3 characters long.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        if document_type not in ['deed', 'survey', 'tax_certificate', 'identity', 'other']:
            flash('Please select a valid document type.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        # Handle file upload
        if 'document_file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        file = request.files['document_file']
        
        # Validate file using security module
        is_valid, result = validate_file(
            file, 
            allowed_extensions=app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}),
            max_size=app.config.get('MAX_CONTENT_LENGTH', 16*1024*1024)
        )
        
        if not is_valid:
            flash(f'File validation failed: {result}', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        try:
            # Read file content and calculate hash
            file_content = file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file_size = len(file_content)
            
            # Check for duplicate files
            existing_doc = conn.execute(
            'SELECT id FROM documents WHERE file_hash = ? AND property_id = ?',
            (file_hash, property_id)
        ).fetchone()
            
            if existing_doc:
                flash('This file has already been uploaded for this property.', 'warning')
                return render_template('upload_documents.html', property=property_data, documents=documents)
            
            # Reset file pointer for saving
            file.seek(0)
            
            # Sanitize and secure filename
            filename = sanitize_filename(result)  # result contains the secure filename from validate_file
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Log file upload
            app.logger.info(f'File uploaded: {filename} by user {session["user_id"]} for property {property_id}')
            
            # Determine verification status
            verification_status = 'verified' if auto_verify else 'pending'
            
            # Insert document record
            cursor = conn.execute('''
                INSERT INTO documents 
                (property_id, document_type, document_title, file_path, file_size, uploaded_by, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (property_id, document_type, document_title, file_path, 
                  file_size, session['user_id'], verification_status))
            
            document_id = cursor.lastrowid
            
            # Store on blockchain if requested
            if blockchain_store:
                # Create blockchain entry for document
                document_data = {
                    'type': 'document_upload',
                    'document_id': document_id,
                    'property_id': property_id,
                    'document_type': document_type,
                    'title': document_title,
                    'file_hash': file_hash,
                    'uploaded_by': session['user_id'],
                    'timestamp': datetime.datetime.now().isoformat(),
                    'verification_status': verification_status
                }
                
                # Get previous block hash
                prev_block = conn.execute(
                    'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
                ).fetchone()
                prev_hash = prev_block['block_hash'] if prev_block else '0'
                
                # Create blockchain entry
                block_hash = calculate_hash(prev_hash + json.dumps(document_data, sort_keys=True))
                
                conn.execute('''
                    INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
                    VALUES (?, ?, ?, ?)
                ''', (block_hash, prev_hash, json.dumps(document_data), 'document_upload'))
            
            # Create notification for admin if requested
            if notify_admin:
                app.logger.info(f"Admin notification: New document uploaded for property {property_id}")
            
            conn.commit()
            
            flash(f'Document "{document_title}" uploaded successfully! Hash: {file_hash[:16]}...', 'success')
            return redirect(url_for('upload_documents', property_id=property_id))
            
        except Exception as e:
            conn.rollback()
            app.logger.error(f'Document upload error: {str(e)}')
            # Clean up uploaded file if database operation failed
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Error uploading document: {str(e)}', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        finally:
            conn.close()
    
    conn.close()
    return render_template('upload_documents.html', property=property_data, documents=documents)

@app.route('/verify_document/<int:document_id>', methods=['POST'])
@login_required
@role_required('admin')
def verify_document(document_id):
    # Rate limiting check
    if not rate_limit_check(f"{request.remote_addr}_admin_action", 20, 3600):  # 20 admin actions per hour
        return jsonify({'success': False, 'message': 'Too many admin actions. Please try again later.'}), 429
    
    conn = get_db_connection()
    
    try:
        # Get document details
        document = conn.execute(
            'SELECT * FROM documents WHERE id = ?', (document_id,)
        ).fetchone()
        
        if not document:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        # Update verification status
        conn.execute('''
            UPDATE documents SET verification_status = ?, verified_by = ?, verified_at = ?
            WHERE id = ?
        ''', ('verified', session['user_id'], datetime.datetime.now().isoformat(), document_id))
        
        # Create blockchain entry for verification
        verification_data = {
            'type': 'document_verification',
            'document_id': document_id,
            'verified_by': session['user_id'],
            'file_hash': document['file_hash'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Get previous block hash
        prev_block = conn.execute(
            'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
        ).fetchone()
        prev_hash = prev_block['block_hash'] if prev_block else '0'
        
        block_hash = calculate_hash(prev_hash + json.dumps(verification_data, sort_keys=True))
        
        conn.execute('''
            INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
            VALUES (?, ?, ?, ?)
        ''', (block_hash, prev_hash, json.dumps(verification_data), 'document_verification'))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Document verified successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error verifying document: {str(e)}'})
    finally:
        conn.close()

@app.route('/ledger')
def ledger():
    conn = get_db_connection()
    
    try:
        # Get blockchain entries
        blockchain_entries = conn.execute('''
            SELECT * FROM blockchain 
            ORDER BY timestamp DESC
        ''').fetchall()
        
        # Parse JSON data for each entry
        parsed_entries = []
        for entry in blockchain_entries:
            entry_dict = dict(entry)
            try:
                entry_dict['data'] = json.loads(entry_dict['data'])
            except:
                entry_dict['data'] = {}
            parsed_entries.append(entry_dict)
        
        # Get blockchain statistics
        total_blocks = conn.execute('SELECT COUNT(*) as count FROM blockchain').fetchone()['count']
        total_transactions = conn.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
        total_properties = conn.execute('SELECT COUNT(*) as count FROM land_records').fetchone()['count']
        total_documents = conn.execute('SELECT COUNT(*) as count FROM documents WHERE verification_status = "verified"').fetchone()['count']
        
        blockchain_stats = {
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'total_properties': total_properties,
            'total_documents': total_documents
        }
        
        return render_template('ledger.html', 
                             blockchain_entries=parsed_entries,
                             blockchain_stats=blockchain_stats)
        
    except Exception as e:
        flash(f'Error loading ledger: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/purchase_property/<int:property_id>', methods=['POST'])
@login_required
@role_required('buyer')
def purchase_property(property_id):
    # Rate limiting check
    if not rate_limit_check(f"{request.remote_addr}_purchase", 5, 3600):  # 5 purchases per hour
        return jsonify({'success': False, 'message': 'Too many purchase attempts. Please try again later.'}), 429
    
    conn = get_db_connection()
    
    try:
        # Get property details
        property_data = conn.execute('''
            SELECT l.*, u.full_name as owner_name, u.email as owner_email
            FROM land_records l
            JOIN users u ON l.owner_id = u.id
            WHERE l.id = ?
        ''', (property_id,)).fetchone()
        
        if not property_data:
            return jsonify({'success': False, 'message': 'Property not found'})
        
        # Check if property is available (no pending/completed transactions)
        existing_transaction = conn.execute('''
            SELECT * FROM transactions 
            WHERE property_id = ? AND status IN ('pending', 'approved', 'completed')
        ''', (property_id,)).fetchone()
        
        if existing_transaction:
            return jsonify({'success': False, 'message': 'Property is not available for purchase'})
        
        # Get buyer details
        buyer = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not buyer:
            return jsonify({'success': False, 'message': 'Buyer not found'})
        
        # Create transaction record
        conn.execute('''
            INSERT INTO transactions 
            (property_id, seller_id, buyer_email, buyer_phone, payment_method, sale_price, transfer_date, registration_fee, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            property_id,
            property_data['owner_id'],
            buyer['email'],
            buyer['phone'],  # Include buyer's phone number
            'pending_payment',  # Payment method to be determined
            property_data['market_value'],
            datetime.date.today().isoformat(),
            5000,  # Standard registration fee
            'pending'
        ))
        
        transaction_id = conn.lastrowid
        
        # Create blockchain entry for purchase initiation
        purchase_data = {
            'type': 'purchase_initiated',
            'transaction_id': transaction_id,
            'property_id': property_id,
            'buyer_id': session['user_id'],
            'seller_id': property_data['owner_id'],
            'purchase_price': property_data['market_value'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Get previous block hash
        prev_block = conn.execute(
            'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
        ).fetchone()
        prev_hash = prev_block['block_hash'] if prev_block else '0'
        
        block_hash = calculate_hash(prev_hash + json.dumps(purchase_data, sort_keys=True))
        
        conn.execute('''
            INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
            VALUES (?, ?, ?, ?)
        ''', (block_hash, prev_hash, json.dumps(purchase_data), 'purchase_initiated'))
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Purchase request submitted successfully! Your transaction is now pending approval.',
            'transaction_id': transaction_id
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error processing purchase: {str(e)}'})
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)