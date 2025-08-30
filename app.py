from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blockchain_land_management_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///land_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model with role-based access
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, government, seller, buyer
    approved = db.Column(db.Boolean, default=False)  # For buyer/seller approval by admin
    lands = db.relationship('Land', backref='owner', lazy=True)
    purchases = db.relationship('Transaction', backref='buyer', lazy=True, foreign_keys='Transaction.buyer_id')

# Land listing model
class Land(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sold = db.Column(db.Boolean, default=False)
    transactions = db.relationship('Transaction', backref='land', lazy=True)

# Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    land_id = db.Column(db.Integer, db.ForeignKey('land.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    blockchain_record = db.Column(db.String(50), nullable=True)  # Simulated blockchain record
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')

# Routes
@app.route('/')
def home():
    # Get approved transactions with blockchain records for public view
    public_transactions = Transaction.query.filter_by(status='approved').order_by(Transaction.timestamp.desc()).all()
    return render_template('index.html', public_transactions=public_transactions)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        
        # Admin and Government roles are auto-approved, Buyer/Seller need admin approval
        approved = role in ['admin', 'government']
        
        new_user = User(username=username, password=hashed_password, role=role, approved=approved)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! ' + 
              ('You can now log in.' if approved else 'Please wait for admin approval.'))
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            if not user.approved:
                flash('Your account is pending approval by an admin.')
                return redirect(url_for('login'))
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'government':
                return redirect(url_for('government_dashboard'))
            elif user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            elif user.role == 'buyer':
                return redirect(url_for('buyer_dashboard'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    pending_users = User.query.filter_by(approved=False).all()
    all_users = User.query.all()
    
    user_counts = {
        'total': len(all_users),
        'admin': len([u for u in all_users if u.role == 'admin']),
        'government': len([u for u in all_users if u.role == 'government']),
        'seller': len([u for u in all_users if u.role == 'seller']),
        'buyer': len([u for u in all_users if u.role == 'buyer']),
        'pending': len(pending_users)
    }
    
    return render_template('admin_dashboard.html', pending_users=pending_users, all_users=all_users, user_counts=user_counts)

@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    
    flash(f'User {user.username} has been approved!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Update user information
    user.username = request.form.get('username')
    
    # Only update password if provided
    password = request.form.get('password')
    if password and password.strip():
        user.password = generate_password_hash(password)
    
    user.role = request.form.get('role')
    user.approved = 'approved' in request.form
    
    db.session.commit()
    
    flash(f'User {user.username} has been updated!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting the last admin
    if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        flash('Cannot delete the last admin user!')
        return redirect(url_for('admin_dashboard'))
    
    # Delete associated transactions
    Transaction.query.filter((Transaction.buyer_id == user_id) | (Transaction.seller_id == user_id)).delete()
    
    # Delete associated lands
    Land.query.filter_by(owner_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted!')
    return redirect(url_for('admin_dashboard'))

# Government Official routes
@app.route('/government/dashboard')
def government_dashboard():
    if session.get('role') != 'government':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    pending_transactions = Transaction.query.filter_by(status='pending').all()
    approved_transactions = Transaction.query.filter_by(status='approved').all()
    
    return render_template('government_dashboard.html', 
                           pending_transactions=pending_transactions,
                           approved_transactions=approved_transactions)

@app.route('/government/approve_transaction/<int:transaction_id>')
def approve_transaction(transaction_id):
    if session.get('role') != 'government':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    transaction = Transaction.query.get_or_404(transaction_id)
    transaction.status = 'approved'
    
    # Generate a simulated blockchain record
    blockchain_id = f'BLK{random.randint(10000, 99999)}'
    transaction.blockchain_record = blockchain_id
    
    # Update the land as sold
    land = Land.query.get(transaction.land_id)
    land.sold = True
    
    db.session.commit()
    
    flash(f'Transaction approved! Blockchain Record #{blockchain_id} generated.')
    return redirect(url_for('government_dashboard'))

@app.route('/government/reject_transaction/<int:transaction_id>')
def reject_transaction(transaction_id):
    if session.get('role') != 'government':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    transaction = Transaction.query.get_or_404(transaction_id)
    transaction.status = 'rejected'
    db.session.commit()
    
    flash('Transaction rejected!')
    return redirect(url_for('government_dashboard'))

# Seller routes
@app.route('/seller/dashboard')
def seller_dashboard():
    if session.get('role') != 'seller':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    user_id = session.get('user_id')
    lands = Land.query.filter_by(owner_id=user_id).all()
    
    # Get transactions for lands owned by this seller
    transactions = Transaction.query.filter_by(seller_id=user_id).all()
    
    return render_template('seller_dashboard.html', lands=lands, transactions=transactions)

@app.route('/seller/add_land', methods=['GET', 'POST'])
def add_land():
    if session.get('role') != 'seller':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        location = request.form.get('location')
        price = float(request.form.get('price'))
        description = request.form.get('description')
        
        new_land = Land(
            title=title,
            location=location,
            price=price,
            description=description,
            owner_id=session.get('user_id')
        )
        
        db.session.add(new_land)
        db.session.commit()
        
        flash('Land listing added successfully!')
        return redirect(url_for('seller_dashboard'))
    
    return render_template('add_land.html')

# Buyer routes
@app.route('/buyer/dashboard')
def buyer_dashboard():
    if session.get('role') != 'buyer':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    # Available lands (not sold)
    available_lands = Land.query.filter_by(sold=False).all()
    
    # Lands this buyer has purchased
    user_id = session.get('user_id')
    purchases = Transaction.query.filter_by(buyer_id=user_id).all()
    
    return render_template('buyer_dashboard.html', 
                           available_lands=available_lands, 
                           purchases=purchases)

@app.route('/buyer/buy_land/<int:land_id>')
def buy_land(land_id):
    if session.get('role') != 'buyer':
        flash('Unauthorized access!')
        return redirect(url_for('home'))
    
    land = Land.query.get_or_404(land_id)
    
    if land.sold:
        flash('This land is already sold!')
        return redirect(url_for('buyer_dashboard'))
    
    # Create a new transaction
    new_transaction = Transaction(
        land_id=land.id,
        seller_id=land.owner_id,
        buyer_id=session.get('user_id'),
        status='pending'
    )
    
    db.session.add(new_transaction)
    db.session.commit()
    
    flash('Purchase request submitted! Waiting for government approval.')
    return redirect(url_for('buyer_dashboard'))

# Initialize the database
@app.cli.command('init-db')
def init_db():
    db.create_all()
    
    # Create an admin user if none exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin'),
            role='admin',
            approved=True
        )
        db.session.add(admin_user)
        
        # Create a government official if none exists
        govt_user = User(
            username='government',
            password=generate_password_hash('government'),
            role='government',
            approved=True
        )
        db.session.add(govt_user)
        
        db.session.commit()
        print('Database initialized with admin and government users.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default users if they don't exist
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin'),
                role='admin',
                approved=True
            )
            db.session.add(admin_user)
            
            # Create a government official
            govt_user = User(
                username='government',
                password=generate_password_hash('government'),
                role='government',
                approved=True
            )
            db.session.add(govt_user)
            
            # Create a sample seller
            seller_user = User(
                username='seller',
                password=generate_password_hash('seller'),
                role='seller',
                approved=True
            )
            db.session.add(seller_user)
            
            # Create a sample buyer
            buyer_user = User(
                username='buyer',
                password=generate_password_hash('buyer'),
                role='buyer',
                approved=True
            )
            db.session.add(buyer_user)
            
            db.session.commit()
            print('Database initialized with default users.')
    
    app.run(debug=True)