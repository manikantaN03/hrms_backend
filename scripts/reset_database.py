# server/scripts/reset_database.py

"""
Complete database reset - removes everything
⚠️ WARNING: This will delete ALL data and objects!
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Complete database reset"""
    print("\n" + "=" * 70)
    print("⚠️  COMPLETE DATABASE RESET")
    print("=" * 70)
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("\nThis will DELETE:")
    print("  • All tables")
    print("  • All indexes")
    print("  • All enum types")
    print("  • All constraints")
    print("  • ALL DATA")
    print("=" * 70)
    
    confirm = input("\nType 'yes' to confirm (or press Ctrl+C to cancel): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        logger.info("Operation cancelled")
        return False
    
    try:
        with engine.connect() as conn:
            # Step 1: Drop all views (if any)
            logger.info("\n1. Dropping all views...")
            result = conn.execute(text("""
                SELECT viewname 
                FROM pg_views 
                WHERE schemaname = 'public'
            """))
            views = [row[0] for row in result]
            for view in views:
                conn.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE"))
                conn.commit()
            logger.info(f"   ✓ Dropped {len(views)} views")
            
            # Step 2: Drop all tables
            logger.info("\n2. Dropping all tables...")
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                conn.commit()
            logger.info(f"   ✓ Dropped {len(tables)} tables")
            
            # Step 3: Drop all sequences
            logger.info("\n3. Dropping all sequences...")
            result = conn.execute(text("""
                SELECT sequencename 
                FROM pg_sequences 
                WHERE schemaname = 'public'
            """))
            sequences = [row[0] for row in result]
            for seq in sequences:
                conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq} CASCADE"))
                conn.commit()
            logger.info(f"   ✓ Dropped {len(sequences)} sequences")
            
            # Step 4: Drop all enum types
            logger.info("\n4. Dropping all enum types...")
            result = conn.execute(text("""
                SELECT t.typname
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                GROUP BY t.typname
            """))
            enums = [row[0] for row in result]
            for enum in enums:
                conn.execute(text(f"DROP TYPE IF EXISTS {enum} CASCADE"))
                conn.commit()
            logger.info(f"   ✓ Dropped {len(enums)} enum types")
            
            # Step 5: Drop all remaining types
            logger.info("\n5. Dropping all remaining types...")
            conn.execute(text("DROP TYPE IF EXISTS user_role_enum CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS user_status_enum CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS userstatus CASCADE"))
            conn.commit()
            logger.info("   ✓ Dropped all enum types")
            
            # Step 6: Verify everything is gone
            logger.info("\n6. Verifying cleanup...")
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            table_count = result.fetchone()[0]
            
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """))
            index_count = result.fetchone()[0]
            
            if table_count == 0 and index_count == 0:
                logger.info("   ✓ Database is completely clean")
            else:
                logger.warning(f"   ⚠️  {table_count} tables, {index_count} indexes remaining")
        
        print("\n" + "=" * 70)
        print("✓ Database reset complete!")
        print("=" * 70)
        print("\nNext step:")
        print("  python scripts/setup.py")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = reset_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)