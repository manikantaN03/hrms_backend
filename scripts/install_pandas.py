"""
Install pandas for CSV data processing during setup
"""

import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def install_pandas():
    """Install pandas for CSV processing"""
    logger.info("📦 Installing pandas for CSV data processing...")
    
    try:
        import pandas
        logger.info("✅ Pandas already installed")
        return True
    except ImportError:
        pass
    
    try:
        logger.info("📥 Installing pandas...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pandas'], check=True)
        logger.info("✅ Pandas installed successfully")
        
        # Verify installation
        import pandas
        logger.info(f"✅ Pandas version: {pandas.__version__}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install pandas: {e}")
        return False
    except ImportError:
        logger.error("❌ Pandas installation failed - import error")
        return False

if __name__ == "__main__":
    success = install_pandas()
    if success:
        logger.info("\n🎉 Pandas is ready! You can now run setup.py")
        logger.info("Next: python scripts/setup.py")
    else:
        logger.error("\n❌ Pandas installation failed")
        logger.info("Try manually: pip install pandas")
    
    sys.exit(0 if success else 1)