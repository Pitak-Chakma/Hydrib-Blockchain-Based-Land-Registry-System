import sqlite3
import hashlib

def check_and_create_demo_accounts():
    conn = sqlite3.connect('land_registry.db')
    cursor = conn.cursor()
    
    # Check existing demo accounts
    demo_emails = ['admin@hydrib.gov.bd', 'owner@example.com', 'buyer@example.com']
    cursor.execute('SELECT email, role FROM users WHERE email IN (?, ?, ?)', demo_emails)
    existing_accounts = cursor.fetchall()
    
    print('Existing demo accounts in database:')
    for account in existing_accounts:
        print(f'  {account[0]} - {account[1]}')
    
    existing_emails = [account[0] for account in existing_accounts]
    
    # Create missing demo accounts
    demo_accounts = [
        ('admin@hydrib.gov.bd', 'admin123', 'admin', 'Government Official'),
        ('owner@example.com', 'owner123', 'owner', 'Demo Landowner'),
        ('buyer@example.com', 'buyer123', 'buyer', 'Demo Buyer')
    ]
    
    created_count = 0
    for email, password, role, name in demo_accounts:
        if email not in existing_emails:
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, email, password_hash, role))
            
            print(f'Created demo account: {email} ({role})')
            created_count += 1
    
    if created_count > 0:
        conn.commit()
        print(f'\nSuccessfully created {created_count} demo accounts.')
    else:
        print('\nAll demo accounts already exist.')
    
    conn.close()

if __name__ == '__main__':
    check_and_create_demo_accounts()