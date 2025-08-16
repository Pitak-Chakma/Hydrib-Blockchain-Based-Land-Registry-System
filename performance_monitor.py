#!/usr/bin/env python3
"""
Performance Monitoring Script for Hydrib Land Registry System
Monitors database query performance and identifies bottlenecks
"""

import sqlite3
import time
import json
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('land_registry.db')
    conn.row_factory = sqlite3.Row
    return conn

def measure_query_performance(query, params=None, description=""):
    """
    Measure the execution time of a database query
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    
    try:
        if params:
            result = cursor.execute(query, params).fetchall()
        else:
            result = cursor.execute(query).fetchall()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'description': description,
            'query': query[:100] + '...' if len(query) > 100 else query,
            'execution_time': execution_time,
            'result_count': len(result),
            'status': 'success'
        }
    
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'description': description,
            'query': query[:100] + '...' if len(query) > 100 else query,
            'execution_time': execution_time,
            'result_count': 0,
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        conn.close()

def test_common_queries():
    """
    Test performance of common application queries
    """
    print("🔍 Testing Common Query Performance...")
    print("=" * 50)
    
    queries = [
        {
            'query': 'SELECT * FROM users WHERE email = ?',
            'params': ('admin@hydrib.gov.bd',),
            'description': 'User login query'
        },
        {
            'query': '''SELECT l.*, u.full_name as owner_name 
                       FROM land_records l 
                       JOIN users u ON l.owner_id = u.id 
                       ORDER BY l.created_at DESC LIMIT 10''',
            'params': None,
            'description': 'Recent land records with owner info'
        },
        {
            'query': '''SELECT t.*, l.plot_number 
                       FROM transactions t 
                       JOIN land_records l ON t.property_id = l.id 
                       WHERE t.status = ? 
                       ORDER BY t.created_at DESC''',
            'params': ('pending',),
            'description': 'Pending transactions'
        },
        {
            'query': '''SELECT * FROM blockchain 
                       ORDER BY timestamp DESC LIMIT 20''',
            'params': None,
            'description': 'Recent blockchain entries'
        },
        {
            'query': '''SELECT COUNT(*) as count FROM land_records 
                       WHERE division = ? AND district = ?''',
            'params': ('Dhaka', 'Dhaka'),
            'description': 'Location-based property count'
        },
        {
            'query': '''SELECT d.*, l.plot_number 
                       FROM documents d 
                       JOIN land_records l ON d.property_id = l.id 
                       WHERE d.verification_status = ?''',
            'params': ('pending',),
            'description': 'Pending document verifications'
        },
        {
            'query': '''SELECT u.role, COUNT(*) as count 
                       FROM users u 
                       GROUP BY u.role''',
            'params': None,
            'description': 'User role statistics'
        },
        {
            'query': '''SELECT t.status, COUNT(*) as count, AVG(t.sale_price) as avg_price 
                       FROM transactions t 
                       GROUP BY t.status''',
            'params': None,
            'description': 'Transaction statistics'
        }
    ]
    
    results = []
    total_time = 0
    
    for query_info in queries:
        result = measure_query_performance(
            query_info['query'], 
            query_info.get('params'), 
            query_info['description']
        )
        results.append(result)
        total_time += result['execution_time']
        
        status_icon = "✓" if result['status'] == 'success' else "✗"
        print(f"{status_icon} {result['description']}: {result['execution_time']:.4f}s ({result['result_count']} rows)")
        
        if result['status'] == 'error':
            print(f"   Error: {result['error']}")
    
    print(f"\n📊 Total execution time: {total_time:.4f}s")
    print(f"📊 Average query time: {total_time/len(queries):.4f}s")
    
    return results

def analyze_query_plans():
    """
    Analyze query execution plans for optimization opportunities
    """
    print("\n🔬 Analyzing Query Execution Plans...")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    complex_queries = [
        {
            'query': '''SELECT l.*, u.full_name as owner_name 
                       FROM land_records l 
                       JOIN users u ON l.owner_id = u.id 
                       ORDER BY l.created_at DESC''',
            'description': 'Land records with owner JOIN'
        },
        {
            'query': '''SELECT t.*, l.plot_number, u.full_name as seller_name 
                       FROM transactions t 
                       JOIN land_records l ON t.property_id = l.id 
                       JOIN users u ON t.seller_id = u.id 
                       WHERE t.status = 'pending' 
                       ORDER BY t.created_at DESC''',
            'description': 'Complex transaction query with multiple JOINs'
        },
        {
            'query': '''SELECT d.*, l.plot_number, l.address 
                       FROM documents d 
                       JOIN land_records l ON d.property_id = l.id 
                       WHERE d.verification_status = 'pending' 
                       ORDER BY d.uploaded_at DESC''',
            'description': 'Document verification query'
        }
    ]
    
    for query_info in complex_queries:
        print(f"\n📋 {query_info['description']}:")
        try:
            plan = cursor.execute(f"EXPLAIN QUERY PLAN {query_info['query']}").fetchall()
            for step in plan:
                print(f"   {step[3]}")
        except Exception as e:
            print(f"   Error analyzing query plan: {e}")
    
    conn.close()

def check_index_usage():
    """
    Check which indexes are being used effectively
    """
    print("\n📈 Index Usage Analysis...")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all indexes
        indexes = cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchall()
        
        print(f"📊 Found {len(indexes)} custom indexes:")
        for index in indexes:
            print(f"   • {index[0]} on {index[1]}")
        
        # Check table statistics
        print("\n📊 Table Statistics:")
        tables = ['users', 'land_records', 'transactions', 'documents', 'blockchain']
        
        for table in tables:
            try:
                count = cursor.execute(f'SELECT COUNT(*) as count FROM {table}').fetchone()[0]
                print(f"   • {table}: {count} records")
            except Exception as e:
                print(f"   • {table}: Error - {e}")
    
    except Exception as e:
        print(f"Error checking indexes: {e}")
    
    finally:
        conn.close()

def generate_performance_report():
    """
    Generate a comprehensive performance report
    """
    print("\n📄 Generating Performance Report...")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'query_performance': test_common_queries(),
        'recommendations': []
    }
    
    # Analyze results and generate recommendations
    slow_queries = [q for q in report['query_performance'] if q['execution_time'] > 0.1]
    
    if slow_queries:
        report['recommendations'].append({
            'type': 'performance',
            'message': f"Found {len(slow_queries)} queries taking >100ms",
            'queries': [q['description'] for q in slow_queries]
        })
    
    # Check for queries with many results that might need pagination
    large_result_queries = [q for q in report['query_performance'] if q['result_count'] > 100]
    
    if large_result_queries:
        report['recommendations'].append({
            'type': 'pagination',
            'message': f"Found {len(large_result_queries)} queries returning >100 rows",
            'queries': [q['description'] for q in large_result_queries]
        })
    
    # Save report to file
    report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Performance report saved to: {report_filename}")
    except Exception as e:
        print(f"\n❌ Error saving report: {e}")
    
    return report

def monitor_real_time_performance(duration_seconds=60):
    """
    Monitor database performance in real-time
    """
    print(f"\n⏱️  Real-time Performance Monitoring ({duration_seconds}s)...")
    print("=" * 50)
    
    start_time = time.time()
    query_times = []
    
    test_query = "SELECT COUNT(*) FROM users"
    
    while time.time() - start_time < duration_seconds:
        result = measure_query_performance(test_query, description="Health check")
        query_times.append(result['execution_time'])
        
        print(f"\r⏱️  Query time: {result['execution_time']:.4f}s | Avg: {sum(query_times)/len(query_times):.4f}s", end="")
        time.sleep(1)
    
    print(f"\n\n📊 Real-time monitoring completed:")
    print(f"   • Total queries: {len(query_times)}")
    print(f"   • Average time: {sum(query_times)/len(query_times):.4f}s")
    print(f"   • Min time: {min(query_times):.4f}s")
    print(f"   • Max time: {max(query_times):.4f}s")

if __name__ == '__main__':
    print("🚀 Hydrib Performance Monitor")
    print("=" * 50)
    
    # Test common queries
    test_common_queries()
    
    # Analyze query plans
    analyze_query_plans()
    
    # Check index usage
    check_index_usage()
    
    # Generate comprehensive report
    generate_performance_report()
    
    print("\n✅ Performance monitoring completed!")
    print("\n💡 Recommendations:")
    print("   1. Run this script regularly to monitor performance trends")
    print("   2. Review slow queries and consider optimization")
    print("   3. Monitor index usage and add indexes for frequently queried columns")
    print("   4. Implement query result caching for expensive operations")
    print("   5. Consider database connection pooling for production")