"""
Database Tables Verification
Lists all tables and their row counts
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings


def check_tables():
    """Display all database tables and their contents."""
    
    print("\n" + "=" * 70)
    print("DATABASE TABLES CHECK")
    print("=" * 70)
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 70)
    
    try:
        with engine.connect() as conn:
            # Get all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if not tables:
                print("\n✗ No tables found in database!")
                print("\nCreate tables with:")
                print("  python scripts/init_db.py")
                return False
            
            print(f"\n✓ Found {len(tables)} table(s):\n")
            
            for table in tables:
                # Get column count
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                """))
                col_count = result.fetchone()[0]
                
                # Get row count
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                row_count = result.fetchone()[0]
                
                print(f"  {table}")
                print(f"    Columns: {col_count}")
                print(f"    Rows: {row_count}")
                print()
            
            print("=" * 70)
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_tables()
    sys.exit(0 if success else 1)