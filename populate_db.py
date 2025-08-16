#!/usr/bin/env python3
"""
Script to populate the database with sample data for testing the land registry system.
"""

import sqlite3
import hashlib
import datetime
from werkzeug.security import generate_password_hash

def get_db_connection():
    conn = sqlite3.connect('land_registry.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_hash(data):
    return hashlib.sha256(str(data).encode()).hexdigest()

def populate_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    cursor.execute('DELETE FROM documents')
    cursor.execute('DELETE FROM transactions')
    cursor.execute('DELETE FROM blockchain')
    cursor.execute('DELETE FROM land_records')
    cursor.execute('DELETE FROM users')
    
    # Sample users - including the required demo accounts
    users = [
        {
            'email': 'admin@hydrib.gov.bd',  # Required demo account
            'password': 'admin123',
            'role': 'admin',
            'full_name': 'Government Official',
            'phone': '+880-1711-123456'
        },
        {
            'email': 'owner@example.com',  # Required demo account
            'password': 'owner123',
            'role': 'owner',
            'full_name': 'Demo Landowner',
            'phone': '+880-1712-234567'
        },
        {
            'email': 'buyer@example.com',  # Required demo account
            'password': 'buyer123',
            'role': 'buyer',
            'full_name': 'Demo Buyer',
            'phone': '+880-1713-345678'
        },
        {
            'email': 'ahmed.rahman@email.com',
            'password': 'owner123',
            'role': 'owner',
            'full_name': 'Ahmed Rahman',
            'phone': '+880-1714-456789'
        },
        {
            'email': 'fatima.khatun@email.com',
            'password': 'owner123',
            'role': 'owner',
            'full_name': 'Fatima Khatun',
            'phone': '+880-1715-567890'
        },
        {
            'email': 'mohammad.islam@email.com',
            'password': 'owner123',
            'role': 'owner',
            'full_name': 'Mohammad Islam',
            'phone': '+880-1716-678901'
        },
        {
            'email': 'buyer1@email.com',
            'password': 'buyer123',
            'role': 'buyer',
            'full_name': 'Rashida Begum',
            'phone': '+880-1717-789012'
        }
    ]
    
    # Insert users
    user_ids = {}
    for user in users:
        password_hash = generate_password_hash(user['password'])
        cursor.execute(
            'INSERT INTO users (email, password_hash, role, full_name, phone) VALUES (?, ?, ?, ?, ?)',
            (user['email'], password_hash, user['role'], user['full_name'], user['phone'])
        )
        user_ids[user['email']] = cursor.lastrowid
    
    # Sample land records
    land_records = [
        {
            'plot_number': 'DHAKA-001',
            'location': 'Dhanmondi, Dhaka',
            'area': 2.5,
            'owner_email': 'owner@example.com',  # Demo landowner
            'document_hash': calculate_hash('deed_dhaka_001_2024'),
            'status': 'active'
        },
        {
            'plot_number': 'CTG-002',
            'location': 'Agrabad, Chittagong',
            'area': 1.8,
            'owner_email': 'owner@example.com',  # Demo landowner
            'document_hash': calculate_hash('deed_ctg_002_2024'),
            'status': 'active'
        },
        {
            'plot_number': 'SYL-003',
            'location': 'Zindabazar, Sylhet',
            'area': 3.2,
            'owner_email': 'ahmed.rahman@email.com',
            'document_hash': calculate_hash('deed_syl_003_2024'),
            'status': 'active'
        },
        {
            'plot_number': 'DHAKA-004',
            'location': 'Gulshan, Dhaka',
            'area': 1.5,
            'owner_email': 'ahmed.rahman@email.com',
            'document_hash': calculate_hash('deed_dhaka_004_2024'),
            'status': 'active'
        },
        {
            'plot_number': 'RAJ-005',
            'location': 'Shaheb Bazar, Rajshahi',
            'area': 4.0,
            'owner_email': 'fatima.khatun@email.com',
            'document_hash': calculate_hash('deed_raj_005_2024'),
            'status': 'pending_transfer'
        },
        {
            'plot_number': 'KHU-006',
            'location': 'Sonadanga, Khulna',
            'area': 2.8,
            'owner_email': 'mohammad.islam@email.com',
            'document_hash': calculate_hash('deed_khu_006_2024'),
            'status': 'active'
        }
    ]
    
    # Insert land records
    land_ids = {}
    for land in land_records:
        owner_id = user_ids[land['owner_email']]
        cursor.execute(
            'INSERT INTO land_records (plot_number, area, owner_id, status, address, land_type, division, district, upazila, market_value, hash_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (land['plot_number'], land['area'], owner_id, land['status'], land['location'], 'residential', 'Dhaka', 'Dhaka', 'Dhanmondi', 5000000, 'sample_hash_' + land['plot_number'])
        )
        land_ids[land['plot_number']] = cursor.lastrowid
    
    # Sample transactions
    transactions = [
        {
            'land_plot': 'DHAKA-001',
            'from_user': None,  # Registration transaction
            'to_user': 'owner@example.com',  # Demo landowner
            'transaction_type': 'registration',
            'price': None,
            'status': 'completed',
            'smart_contract_result': 'Registration verified and approved',
            'consensus_votes': 1,
            'required_votes': 1
        },
        {
            'land_plot': 'CTG-002',
            'from_user': None,
            'to_user': 'owner@example.com',  # Demo landowner
            'transaction_type': 'registration',
            'price': None,
            'status': 'completed',
            'smart_contract_result': 'Registration verified and approved',
            'consensus_votes': 1,
            'required_votes': 1
        },
        {
            'land_plot': 'RAJ-005',
            'from_user': 'fatima.khatun@email.com',
            'to_user': 'buyer@example.com',  # Demo buyer
            'transaction_type': 'sale',
            'price': 8500000.00,  # 85 lakh BDT
            'status': 'pending',
            'smart_contract_result': 'Awaiting government approval',
            'consensus_votes': 0,
            'required_votes': 1
        },
        {
            'land_plot': 'SYL-003',
            'from_user': 'ahmed.rahman@email.com',
            'to_user': 'buyer@example.com',  # Demo buyer
            'transaction_type': 'sale',
            'price': 6200000.00,  # 62 lakh BDT
            'status': 'approved',
            'smart_contract_result': 'Smart contract conditions met, awaiting final transfer',
            'consensus_votes': 1,
            'required_votes': 1
        },
        {
            'land_plot': 'DHAKA-004',
            'from_user': 'ahmed.rahman@email.com',
            'to_user': 'buyer1@email.com',
            'transaction_type': 'sale',
            'price': 7800000.00,  # 78 lakh BDT
            'status': 'pending',
            'smart_contract_result': 'Verifying buyer credentials and funds',
            'consensus_votes': 0,
            'required_votes': 1
        }
    ]
    
    # Insert transactions
    for transaction in transactions:
        land_id = land_ids[transaction['land_plot']]
        from_user_id = user_ids[transaction['from_user']] if transaction['from_user'] else None
        to_user_id = user_ids[transaction['to_user']]
        
        to_user_email = [email for email, uid in user_ids.items() if uid == to_user_id][0] if to_user_id else 'unknown@example.com'
        
        # Handle registration transactions differently (no sale price)
        if transaction['transaction_type'] == 'registration':
            cursor.execute(
                '''INSERT INTO transactions 
                   (property_id, seller_id, buyer_email, payment_method, sale_price, transfer_date, registration_fee, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (land_id, from_user_id, to_user_email, 'registration', 0, '2024-01-01', 5000, transaction['status'])
            )
        else:
            cursor.execute(
                '''INSERT INTO transactions 
                   (property_id, seller_id, buyer_email, payment_method, sale_price, transfer_date, registration_fee, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (land_id, from_user_id, to_user_email, 'cash', transaction['price'], '2024-01-01', 5000, transaction['status'])
            )
    
    # Sample blockchain entries
    blockchain_entries = [
        {
            'transaction_data': 'Genesis Block - Land Registry System Initialized',
            'previous_hash': '0'
        },
        {
            'transaction_data': f'Land Registration: {land_records[0]["plot_number"]} registered to {users[1]["full_name"]}',
            'previous_hash': calculate_hash('Genesis Block - Land Registry System Initialized')
        },
        {
            'transaction_data': f'Land Registration: {land_records[1]["plot_number"]} registered to {users[2]["full_name"]}',
            'previous_hash': calculate_hash(f'Land Registration: {land_records[0]["plot_number"]} registered to {users[1]["full_name"]}')
        }
    ]
    
    # Insert blockchain entries
    for i, entry in enumerate(blockchain_entries):
        block_hash = calculate_hash(f"{entry['transaction_data']}{entry['previous_hash']}{i}")
        transaction_type = 'genesis' if i == 0 else 'registration'
        cursor.execute(
            'INSERT INTO blockchain (block_hash, previous_hash, data, transaction_type) VALUES (?, ?, ?, ?)',
            (block_hash, entry['previous_hash'], entry['transaction_data'], transaction_type)
        )
    
    conn.commit()
    conn.close()
    
    print("Sample data populated successfully!")
    print("\nDemo Accounts:")
    print("Government Official: admin@hydrib.gov.bd / admin123")
    print("Landowner: owner@example.com / owner123")
    print("Buyer: buyer@example.com / buyer123")
    print("\nAdditional accounts:")
    print("Landowner 1: ahmed.rahman@email.com / owner123")
    print("Landowner 2: fatima.khatun@email.com / owner123")
    print("Landowner 3: mohammad.islam@email.com / owner123")
    print("Buyer 1: buyer1@email.com / buyer123")

if __name__ == '__main__':
    populate_sample_data()