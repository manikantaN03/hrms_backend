"""
Logo Base64 Loader
Loads the Runtime HRMS logo as base64 for embedding in emails
"""

import base64
import os
from pathlib import Path

def get_logo_base64() -> str:
    """
    Get the Runtime HRMS logo as base64 encoded string.
    This allows the logo to be embedded directly in emails.
    
    Returns:
        Base64 encoded string of the logo image
    """
    try:
        # Get the logo file path
        logo_path = Path(__file__).parent.parent.parent / "static" / "images" / "runtime-logo.png"
        
        if not logo_path.exists():
            print(f"Warning: Logo file not found at {logo_path}")
            return None
        
        # Read and encode the logo
        with open(logo_path, "rb") as f:
            logo_data = f.read()
            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            return logo_base64
            
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None

def get_logo_data_url() -> str:
    """
    Get the logo as a data URL for use in img src attribute.
    
    Returns:
        Data URL string like: data:image/png;base64,iVBORw0KG...
    """
    logo_base64 = get_logo_base64()
    if logo_base64:
        return f"data:image/png;base64,{logo_base64}"
    return None

# Cache the logo to avoid reading file multiple times
_cached_logo_base64 = None
_cached_logo_data_url = None

def get_cached_logo_base64() -> str:
    """Get cached base64 logo"""
    global _cached_logo_base64
    if _cached_logo_base64 is None:
        _cached_logo_base64 = get_logo_base64()
    return _cached_logo_base64

def get_cached_logo_data_url() -> str:
    """Get cached data URL logo"""
    global _cached_logo_data_url
    if _cached_logo_data_url is None:
        _cached_logo_data_url = get_logo_data_url()
    return _cached_logo_data_url
