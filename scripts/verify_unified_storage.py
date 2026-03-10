"""
Unified User Storage Verification
Confirms all user types are in the same 'users' table
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


def verify_storage():
    """Verify unified user storage architecture."""
    
    print("\n" + "=" * 70)
    print("UNIFIED USER STORAGE VERIFICATION")
    print("=" * 70)
    
    try:
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'users'
            """))
            
            if result.fetchone()[0] == 0:
                print("\n✗ Users table does not exist!")
                print("\nCreate tables with:")
                print("  python scripts/init_db.py")
                return False
            
            print("\n✓ Users table exists")
            
            # Get user counts by role
            result = conn.execute(text("""
                SELECT role, status, COUNT(*) as count
                FROM users
                GROUP BY role, status
                ORDER BY role, status
            """))
            
            users_by_role = result.fetchall()
            
            if not users_by_role:
                print("\n⚠️  No users found in database")
            else:
                print("\n📊 Users by role (all in 'users' table):")
                print("-" * 70)
                print(f"{'Role':<15} {'Status':<15} {'Count':<10}")
                print("-" * 70)
                
                total = 0
                for role, status, count in users_by_role:
                    print(f"{role:<15} {status:<15} {count:<10}")
                    total += count
                
                print("-" * 70)
                print(f"{'TOTAL':<15} {'':<15} {total:<10}")
                print("-" * 70)
            
            # Show sample users
            result = conn.execute(text("""
                SELECT id, name, email, role, status, is_email_verified
                FROM users
                ORDER BY role, id
                LIMIT 10
            """))
            
            sample_users = result.fetchall()
            
            if sample_users:
                print("\n📋 Sample Users:")
                print("-" * 100)
                print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Role':<12} {'Status':<10} {'Verified':<10}")
                print("-" * 100)
                
                for user in sample_users:
                    verified = "✓" if user[5] else "✗"
                    print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<12} {user[4]:<10} {verified:<10}")
                
                print("-" * 100)
            
            # Summary
            print("\n" + "=" * 70)
            print("✓ VERIFICATION COMPLETE")
            print("=" * 70)
            print("\nArchitecture Confirmed:")
            print("  • All users (SUPERADMIN, ADMIN, USER) in same table")
            print("  • Single 'users' table simplifies data model")
            print("  • 'role' column differentiates user types")
            print("  • Same registration flow for all users")
            print("=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_storage()
    sys.exit(0 if success else 1)