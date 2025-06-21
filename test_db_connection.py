#!/usr/bin/env python3
"""
Simple database connection test script
Run this to test if the database connection is working properly
"""

from database_pool import get_db_cursor
import sys

def test_connection():
    """Test database connection and basic operations"""
    try:
        print("Testing database connection...")
        
        with get_db_cursor() as (conn, cur):
            # Test basic query
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            print(f"✅ Basic query test: {result}")
            
            # Test table existence
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table['table_name']}")
            
            # Test reviewer_data table
            cur.execute("SELECT COUNT(*) as count FROM reviewer_data")
            reviewer_count = cur.fetchone()
            print(f"✅ Reviewer count: {reviewer_count['count']}")
            
            # Test user_data table
            cur.execute("SELECT COUNT(*) as count FROM user_data")
            user_count = cur.fetchone()
            print(f"✅ User count: {user_count['count']}")
            
            # Test reviews_data table
            cur.execute("SELECT COUNT(*) as count FROM reviews_data")
            review_count = cur.fetchone()
            print(f"✅ Review count: {review_count['count']}")
            
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 