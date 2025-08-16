from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('land_registry.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'owner', 'buyer')),
            full_name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Land records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_number TEXT UNIQUE NOT NULL,
            khatian_number TEXT,
            dag_number TEXT,
            land_type TEXT,
            area REAL NOT NULL,
            market_value INTEGER,
            division TEXT,
            district TEXT,
            upazila TEXT,
            mouza TEXT,
            address TEXT,
            description TEXT,
            location TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            document_hash TEXT,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'pending_transfer', 'transferred', 'registered')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    
    # Blockchain simulation table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_hash TEXT UNIQUE NOT NULL,
            previous_hash TEXT,
            transaction_data TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            nonce INTEGER DEFAULT 0
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            land_id INTEGER NOT NULL,
            from_user_id INTEGER,
            to_user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL CHECK (transaction_type IN ('registration', 'transfer', 'sale')),
            price REAL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
            smart_contract_result TEXT,
            consensus_votes INTEGER DEFAULT 0,
            required_votes INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (land_id) REFERENCES land_records (id),
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id)
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            land_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (land_id) REFERENCES land_records (id),
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('land_registry.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_hash(data):
    return hashlib.sha256(str(data).encode()).hexdigest()

def create_block(transaction_data, previous_hash=''):
    timestamp = datetime.datetime.now().isoformat()
    block_data = {
        'transaction_data': transaction_data,
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
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        full_name = request.form['full_name']
        phone = request.form.get('phone', '')
        
        # Validate input
        if not all([email, password, role, full_name]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if role not in ['admin', 'owner', 'buyer']:
            flash('Invalid role selected', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        # Check if user already exists
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email already registered', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (?, ?, ?, ?, ?)',
            (email, password_hash, role, full_name, phone)
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    
    if user_role == 'admin':
        # Admin dashboard - pending transactions and system overview
        pending_transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.location, 
                      u1.full_name as from_user, u2.full_name as to_user
               FROM transactions t
               JOIN land_records l ON t.land_id = l.id
               LEFT JOIN users u1 ON t.from_user_id = u1.id
               JOIN users u2 ON t.to_user_id = u2.id
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
            '''SELECT t.*, l.plot_number, l.location
               FROM transactions t
               JOIN land_records l ON t.land_id = l.id
               WHERE t.from_user_id = ? OR t.to_user_id = ?
               ORDER BY t.created_at DESC LIMIT 10''',
            (user_id, user_id)
        ).fetchall()
        
        conn.close()
        return render_template('owner_dashboard.html', 
                             properties=properties,
                             transactions=transactions)
    
    else:  # buyer
        # Buyer dashboard - available properties and their transactions
        available_properties = conn.execute(
            '''SELECT l.*, u.full_name as owner_name
               FROM land_records l
               JOIN users u ON l.owner_id = u.id
               WHERE l.status = 'active'
               ORDER BY l.created_at DESC'''
        ).fetchall()
        
        my_purchases = conn.execute(
            '''SELECT l.*, t.status as transaction_status
               FROM land_records l
               JOIN transactions t ON l.id = t.land_id
               WHERE t.to_user_id = ? AND t.transaction_type = 'sale'
               ORDER BY t.created_at DESC''',
            (user_id,)
        ).fetchall()
        
        pending_transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.location
               FROM transactions t
               JOIN land_records l ON t.land_id = l.id
               WHERE t.to_user_id = ? AND t.status = 'pending'
               ORDER BY t.created_at DESC''',
            (user_id,)
        ).fetchall()
        
        transactions = conn.execute(
            '''SELECT t.*, l.plot_number, l.location
               FROM transactions t
               JOIN land_records l ON t.land_id = l.id
               WHERE t.to_user_id = ?
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
def register_land():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        plot_number = request.form['plot_number']
        khatian_number = request.form['khatian_number']
        dag_number = request.form['dag_number']
        land_type = request.form['land_type']
        area = float(request.form['area'])
        market_value = int(request.form['market_value'])
        division = request.form['division']
        district = request.form['district']
        upazila = request.form['upazila']
        mouza = request.form['mouza']
        address = request.form['address']
        description = request.form.get('description', '')
        
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
                 division, district, upazila, mouza, address, description, location, owner_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plot_number, khatian_number, dag_number, land_type, area, market_value,
                  division, district, upazila, mouza, address, description, location,
                  session['user_id'], 'registered'))
            
            land_id = cursor.lastrowid
            
            # Get previous block hash
            prev_block = conn.execute(
                'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
            ).fetchone()
            prev_hash = prev_block['block_hash'] if prev_block else '0'
            
            # Create blockchain entry
            block_data = {
                'type': 'land_registration',
                'land_id': land_id,
                'property_data': property_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            block_hash = calculate_hash(prev_hash + json.dumps(block_data, sort_keys=True))
            
            conn.execute('''
                INSERT INTO blockchain (block_hash, previous_hash, transaction_data)
                VALUES (?, ?, ?)
            ''', (block_hash, prev_hash, json.dumps(block_data)))
            
            # Create transaction record
            conn.execute('''
                INSERT INTO transactions 
                (land_id, from_user_id, to_user_id, transaction_type, price, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (land_id, None, session['user_id'], 'registration', 0, 'completed'))
            
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
def transfer_property(property_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get property details and verify ownership
    property_data = conn.execute('''
        SELECT * FROM land_records WHERE id = ? AND owner_id = ?
    ''', (property_id, session['user_id'])).fetchone()
    
    if not property_data:
        flash('Property not found or you do not have permission to transfer it.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        buyer_email = request.form['buyer_email']
        buyer_phone = request.form.get('buyer_phone', '')
        sale_price = int(request.form['sale_price'])
        payment_method = request.form['payment_method']
        transfer_date = request.form['transfer_date']
        registration_fee = int(request.form.get('registration_fee', 5000))
        notes = request.form.get('notes', '')
        
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
                (land_id, from_user_id, to_user_id, transaction_type, price, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (property_id, session['user_id'], buyer['id'], 'sale', sale_price, 'pending'))
            
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
def approve_transaction(transaction_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    
    try:
        # Get transaction details
        transaction = conn.execute('''
            SELECT t.*, l.plot_number, l.owner_id
            FROM transactions t
            JOIN land_records l ON t.land_id = l.id
            WHERE t.id = ?
        ''', (transaction_id,)).fetchone()
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'})
        
        if transaction['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Transaction is not pending'})
        
        # Update transaction status
        conn.execute('''
            UPDATE transactions SET status = ?, approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', ('approved', session['user_id'], datetime.datetime.now().isoformat(), transaction_id))
        
        # If it's a sale transaction, transfer ownership
        if transaction['transaction_type'] == 'sale':
            conn.execute('''
                UPDATE land_records SET owner_id = ?, status = ?
                WHERE id = ?
            ''', (transaction['to_user_id'], 'active', transaction['land_id']))
            
            # Create blockchain entry for ownership transfer
            transfer_data = {
                'type': 'ownership_transfer',
                'transaction_id': transaction_id,
                'property_id': transaction['land_id'],
                'previous_owner': transaction['owner_id'],
                'new_owner': transaction['to_user_id'],
                'sale_price': transaction['price'],
                'approved_by': session['user_id'],
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Get previous block hash
            prev_block = conn.execute(
                'SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1'
            ).fetchone()
            prev_hash = prev_block['block_hash'] if prev_block else '0'
            
            block_hash = calculate_hash(prev_hash + json.dumps(transfer_data, sort_keys=True))
            
            conn.execute('''
                INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type)
                VALUES (?, ?, ?, ?)
            ''', (block_hash, prev_hash, json.dumps(transfer_data), 'ownership_transfer'))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Transaction approved successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error approving transaction: {str(e)}'})
    finally:
        conn.close()

@app.route('/reject_transaction/<int:transaction_id>', methods=['POST'])
def reject_transaction(transaction_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    
    try:
        # Get transaction details
        transaction = conn.execute('''
            SELECT t.*, l.id as land_id
            FROM transactions t
            JOIN land_records l ON t.land_id = l.id
            WHERE t.id = ?
        ''', (transaction_id,)).fetchone()
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'})
        
        if transaction['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Transaction is not pending'})
        
        # Update transaction status
        conn.execute('''
            UPDATE transactions SET status = ?, approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', ('rejected', session['user_id'], datetime.datetime.now().isoformat(), transaction_id))
        
        # Reset property status if it was a sale transaction
        if transaction['transaction_type'] == 'sale':
            conn.execute('''
                UPDATE land_records SET status = ? WHERE id = ?
            ''', ('active', transaction['land_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Transaction rejected successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error rejecting transaction: {str(e)}'})
    finally:
        conn.close()

@app.route('/upload_documents/<int:property_id>', methods=['GET', 'POST'])
def upload_documents(property_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
        SELECT * FROM documents WHERE land_id = ? ORDER BY uploaded_at DESC
    ''', (property_id,)).fetchall()
    
    if request.method == 'POST':
        # Get form data
        document_type = request.form['document_type']
        document_title = request.form['document_title']
        description = request.form.get('description', '')
        document_date = request.form.get('document_date')
        issuing_authority = request.form.get('issuing_authority', '')
        auto_verify = 'auto_verify' in request.form
        blockchain_store = 'blockchain_store' in request.form
        notify_admin = 'notify_admin' in request.form
        
        # Handle file upload
        if 'document_file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        file = request.files['document_file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('upload_documents.html', property=property_data, documents=documents)
        
        if file:
            try:
                # Read file content and calculate hash
                file_content = file.read()
                file_hash = hashlib.sha256(file_content).hexdigest()
                
                # Reset file pointer for saving
                file.seek(0)
                
                # Secure filename
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Determine verification status
                verification_status = 'verified' if auto_verify else 'pending'
                
                # Insert document record
                cursor = conn.execute('''
                    INSERT INTO documents 
                    (land_id, document_type, title, description, file_path, file_hash, 
                     document_date, issuing_authority, verification_status, uploaded_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (property_id, document_type, document_title, description, file_path, 
                      file_hash, document_date, issuing_authority, verification_status, session['user_id']))
                
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
                    # This would typically send an email or create a notification record
                    # For now, we'll just log it
                    print(f"Admin notification: New document uploaded for property {property_id}")
                
                conn.commit()
                
                flash(f'Document "{document_title}" uploaded successfully! Hash: {file_hash[:16]}...', 'success')
                return redirect(url_for('upload_documents', property_id=property_id))
                
            except Exception as e:
                conn.rollback()
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
def verify_document(document_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
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
                entry_dict['data'] = json.loads(entry_dict['transaction_data'])
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)