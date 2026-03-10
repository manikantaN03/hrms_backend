"""
Quick Setup Script - Handles common setup issues automatically
"""

import sys
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required Python packages"""
    logger.info("📦 Installing required dependencies...")
    
    # Core requirements
    core_packages = ['psycopg2-binary', 'sqlalchemy', 'fastapi', 'uvicorn']
    
    # Setup-specific requirements (optional)
    setup_packages = ['pandas']
    
    # Install core packages
    for package in core_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} already installed")
        except ImportError:
            logger.info(f"📥 Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            logger.info(f"✅ {package} installed successfully")
    
    # Install setup packages (non-critical)
    for package in setup_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} already installed")
        except ImportError:
            logger.info(f"📥 Installing {package} (for CSV processing)...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
                logger.info(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                logger.warning(f"⚠️ Failed to install {package}. CSV import will be skipped.")

def run_setup():
    """Run the main setup script"""
    logger.info("🚀 Running main setup script...")
    
    try:
        # Import and run setup after dependencies are installed
        from scripts.setup import main
        success = main()
        return success
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

def main():
    """Main quick setup function"""
    logger.info("🎯 Starting Quick Setup for Levitica HRMS...")
    
    try:
        # Step 1: Install dependencies
        install_dependencies()
        
        # Step 2: Run main setup
        success = run_setup()
        
        if success:
            logger.info("\n🎉 Quick setup completed successfully!")
            logger.info("\nTo start the application:")
            logger.info("  uvicorn app.main:app --reload")
        else:
            logger.error("\n❌ Quick setup failed!")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Quick setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)