import sqlite3
from werkzeug.security import generate_password_hash

def create_demo_accounts():
    conn = sqlite3.connect('land_registry.db')
    cursor = conn.cursor()
    
    # Demo accounts as shown in login.html
    demo_accounts = [
        {
            'email': 'admin@hydrib.gov.bd',
            'password': 'admin123',
            'role': 'admin',
            'full_name': 'Government Official',
            'phone': '+880-1711-000001'
        },
        {
            'email': 'owner@example.com',
            'password': 'owner123',
            'role': 'owner',
            'full_name': 'Demo Landowner',
            'phone': '+880-1711-000002'
        },
        {
            'email': 'buyer@example.com',
            'password': 'buyer123',
            'role': 'buyer',
            'full_name': 'Demo Buyer',
            'phone': '+880-1711-000003'
        }
    ]
    
    print('Checking and creating demo accounts...')
    
    for account in demo_accounts:
        # Check if account already exists
        existing = cursor.execute(
            'SELECT id FROM users WHERE email = ?', 
            (account['email'],)
        ).fetchone()
        
        if existing:
            print(f'Account {account["email"]} already exists')
        else:
            # Create the account
            password_hash = generate_password_hash(account['password'], method='pbkdf2:sha256')
            cursor.execute(
                '''INSERT INTO users (email, password_hash, role, full_name, phone) 
                   VALUES (?, ?, ?, ?, ?)''',
                (account['email'], password_hash, account['role'], 
                 account['full_name'], account['phone'])
            )
            print(f'Created account: {account["email"]} ({account["role"]})')
    
    conn.commit()
    conn.close()
    print('\nDemo accounts setup complete!')
    print('\nYou can now login with:')
    print('Government Official: admin@hydrib.gov.bd / admin123')
    print('Landowner: owner@example.com / owner123')
    print('Buyer: buyer@example.com / buyer123')

if __name__ == '__main__':
    create_demo_accounts()