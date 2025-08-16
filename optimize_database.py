#!/usr/bin/env python3
"""
Database Performance Optimization Script
Adds indexes and optimizations for the Hydrib Land Registry System
"""

import sqlite3
import time

def get_db_connection():
    conn = sqlite3.connect('land_registry.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_performance_indexes():
    """
    Add indexes to improve query performance based on common query patterns
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Adding performance indexes...")
    
    # Indexes for land_records table
    indexes = [
        # For JOIN operations with users table
        "CREATE INDEX IF NOT EXISTS idx_land_records_owner_id ON land_records(owner_id)",
        
        # For created_at ordering
        "CREATE INDEX IF NOT EXISTS idx_land_records_created_at ON land_records(created_at DESC)",
        
        # For plot number lookups
        "CREATE INDEX IF NOT EXISTS idx_land_records_plot_number ON land_records(plot_number)",
        
        # For location-based searches
        "CREATE INDEX IF NOT EXISTS idx_land_records_division_district ON land_records(division, district)",
        
        # Indexes for transactions table
        # For property-based queries
        "CREATE INDEX IF NOT EXISTS idx_transactions_property_id ON transactions(property_id)",
        
        # For seller queries
        "CREATE INDEX IF NOT EXISTS idx_transactions_seller_id ON transactions(seller_id)",
        
        # For buyer email lookups
        "CREATE INDEX IF NOT EXISTS idx_transactions_buyer_email ON transactions(buyer_email)",
        
        # For transaction ordering
        "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC)",
        
        # For status filtering
        "CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)",
        
        # Indexes for documents table
        # For property document lookups
        "CREATE INDEX IF NOT EXISTS idx_documents_property_id ON documents(property_id)",
        
        # For verification status filtering
        "CREATE INDEX IF NOT EXISTS idx_documents_verification_status ON documents(verification_status)",
        
        # For uploader queries
        "CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by)",
        
        # For document type filtering
        "CREATE INDEX IF NOT EXISTS idx_documents_type_status ON documents(document_type, verification_status)",
        
        # Indexes for blockchain table
        # For timestamp ordering (ledger queries)
        "CREATE INDEX IF NOT EXISTS idx_blockchain_timestamp ON blockchain(timestamp DESC)",
        
        # For block hash lookups
        "CREATE INDEX IF NOT EXISTS idx_blockchain_block_hash ON blockchain(block_hash)",
        
        # Indexes for users table
        # Email is already unique, but add index for faster lookups
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        
        # For role-based queries
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        
        # Indexes for admin_notifications table
        # For unread notifications
        "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON admin_notifications(is_read)",
        
        # For notification type filtering
        "CREATE INDEX IF NOT EXISTS idx_notifications_type_created ON admin_notifications(type, created_at DESC)"
    ]
    
    for index_sql in indexes:
        try:
            start_time = time.time()
            cursor.execute(index_sql)
            end_time = time.time()
            index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'
            print(f"✓ Created index idx_{index_name} ({end_time - start_time:.3f}s)")
        except sqlite3.Error as e:
            print(f"✗ Error creating index: {e}")
    
    conn.commit()
    conn.close()
    print("Database indexes optimization completed!")

def analyze_database_performance():
    """
    Analyze current database performance and provide recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\nAnalyzing database performance...")
    
    # Get table sizes
    tables = ['users', 'land_records', 'transactions', 'documents', 'blockchain', 'admin_notifications']
    
    for table in tables:
        try:
            count = cursor.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()['count']
            print(f"📊 {table}: {count} records")
        except sqlite3.Error as e:
            print(f"✗ Error analyzing {table}: {e}")
    
    # Check for missing foreign key constraints
    print("\n🔍 Checking foreign key integrity...")
    
    # Check orphaned land records
    orphaned_lands = cursor.execute('''
        SELECT COUNT(*) as count FROM land_records l 
        LEFT JOIN users u ON l.owner_id = u.id 
        WHERE u.id IS NULL AND l.owner_id IS NOT NULL
    ''').fetchone()['count']
    
    if orphaned_lands > 0:
        print(f"⚠️  Found {orphaned_lands} land records with invalid owner_id")
    else:
        print("✓ All land records have valid owner references")
    
    # Check orphaned transactions
    orphaned_transactions = cursor.execute('''
        SELECT COUNT(*) as count FROM transactions t 
        LEFT JOIN land_records l ON t.property_id = l.id 
        WHERE l.id IS NULL AND t.property_id IS NOT NULL
    ''').fetchone()['count']
    
    if orphaned_transactions > 0:
        print(f"⚠️  Found {orphaned_transactions} transactions with invalid property_id")
    else:
        print("✓ All transactions have valid property references")
    
    # Check orphaned documents
    orphaned_documents = cursor.execute('''
        SELECT COUNT(*) as count FROM documents d 
        LEFT JOIN land_records l ON d.property_id = l.id 
        WHERE l.id IS NULL AND d.property_id IS NOT NULL
    ''').fetchone()['count']
    
    if orphaned_documents > 0:
        print(f"⚠️  Found {orphaned_documents} documents with invalid property_id")
    else:
        print("✓ All documents have valid property references")
    
    conn.close()

def optimize_queries():
    """
    Provide query optimization recommendations
    """
    print("\n📈 Query Optimization Recommendations:")
    print("\n1. Dashboard Queries:")
    print("   - Use LIMIT clauses for large result sets")
    print("   - Consider pagination for transaction lists")
    print("   - Cache frequently accessed statistics")
    
    print("\n2. Search Functionality:")
    print("   - Implement full-text search for property descriptions")
    print("   - Use LIKE with leading wildcards sparingly")
    print("   - Consider search result caching")
    
    print("\n3. Blockchain Queries:")
    print("   - Limit blockchain entries in ledger view")
    print("   - Consider archiving old blockchain entries")
    print("   - Use pagination for large blockchain datasets")
    
    print("\n4. General Recommendations:")
    print("   - Use prepared statements (already implemented)")
    print("   - Consider connection pooling for production")
    print("   - Monitor slow queries with EXPLAIN QUERY PLAN")
    print("   - Regular VACUUM and ANALYZE operations")

def vacuum_database():
    """
    Perform database maintenance operations
    """
    print("\n🧹 Performing database maintenance...")
    
    conn = get_db_connection()
    
    try:
        print("Running VACUUM...")
        conn.execute('VACUUM')
        print("✓ VACUUM completed")
        
        print("Running ANALYZE...")
        conn.execute('ANALYZE')
        print("✓ ANALYZE completed")
        
    except sqlite3.Error as e:
        print(f"✗ Error during maintenance: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Hydrib Database Performance Optimization")
    print("=" * 50)
    
    # Add performance indexes
    add_performance_indexes()
    
    # Analyze current performance
    analyze_database_performance()
    
    # Provide optimization recommendations
    optimize_queries()
    
    # Perform database maintenance
    vacuum_database()
    
    print("\n✅ Database optimization completed!")
    print("\n💡 Next steps:")
    print("   1. Monitor query performance in production")
    print("   2. Implement query result caching where appropriate")
    print("   3. Consider database connection pooling")
    print("   4. Set up regular maintenance schedules")