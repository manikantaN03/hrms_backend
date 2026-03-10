"""
Public Location Information Endpoint
Accessible without authentication for QR code scanning
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.location import Location
from app.models.business import Business
from app.models.employee import Employee

router = APIRouter()


@router.get("/location-info/{location_id}", response_class=HTMLResponse)
async def get_public_location_info(
    location_id: int,
    business_id: int = Query(..., description="Business ID"),
    db: Session = Depends(get_db)
):
    """
    Public endpoint to display location information when QR code is scanned.
    
    **Access:** PUBLIC (No authentication required)
    **Purpose:** Display location details when QR code is scanned
    
    Returns an HTML page with complete location information including:
    - Location name and address
    - Contact information
    - Business details
    - Google Maps integration
    - Employee count at location
    """
    
    # Get location
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == business_id
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Get business information
    business = db.query(Business).filter(Business.id == business_id).first()
    business_name = business.business_name if business else None
    
    # Get employee count at this location
    employee_count = db.query(Employee).filter(
        Employee.location_id == location_id,
        Employee.business_id == business_id,
        Employee.employee_status == "active"
    ).count()
    
    # Get location head and deputy head names (stored as strings in Location model)
    location_head_name = location.location_head if location.location_head else None
    deputy_head_name = location.deputy_head if location.deputy_head else None
    
    # Build Google Maps URL (check if latitude/longitude attributes exist)
    maps_url = None
    if hasattr(location, 'latitude') and hasattr(location, 'longitude'):
        if location.latitude and location.longitude:
            maps_url = f"https://www.google.com/maps/search/?api=1&query={location.latitude},{location.longitude}"
    
    # Generate HTML response
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{location.name} - Location Information</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .container {{
                max-width: 600px;
                width: 100%;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
                animation: slideUp 0.5s ease-out;
            }}
            
            @keyframes slideUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 28px;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            
            .header p {{
                font-size: 14px;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 30px;
            }}
            
            .info-section {{
                margin-bottom: 25px;
            }}
            
            .info-section h2 {{
                font-size: 18px;
                color: #333;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .info-section h2::before {{
                content: '';
                width: 4px;
                height: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 2px;
            }}
            
            .info-item {{
                display: flex;
                padding: 12px 0;
                border-bottom: 1px solid #f0f0f0;
            }}
            
            .info-item:last-child {{
                border-bottom: none;
            }}
            
            .info-label {{
                font-weight: 600;
                color: #666;
                min-width: 140px;
                font-size: 14px;
            }}
            
            .info-value {{
                color: #333;
                flex: 1;
                font-size: 14px;
            }}
            
            .badge {{
                display: inline-block;
                padding: 6px 12px;
                background: #e8f5e9;
                color: #2e7d32;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            
            .badge.inactive {{
                background: #ffebee;
                color: #c62828;
            }}
            
            .map-button {{
                display: inline-block;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-top: 20px;
            }}
            
            .map-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            
            .footer {{
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{location.name}</h1>
                <p>{business_name if business_name else 'Business Information'}</p>
            </div>
            
            <div class="content">
                <div class="info-section">
                    <h2>Location Details</h2>
                    <div class="info-item">
                        <span class="info-label">Location Name:</span>
                        <span class="info-value">{location.name}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">State:</span>
                        <span class="info-value">{location.state or 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Status:</span>
                        <span class="info-value">
                            <span class="badge {'inactive' if not location.is_active else ''}">
                                {'Active' if location.is_active else 'Inactive'}
                            </span>
                        </span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Employees:</span>
                        <span class="info-value">{employee_count} Active</span>
                    </div>
                </div>
                
                {f'''
                <div class="info-section">
                    <h2>Management</h2>
                    {f'<div class="info-item"><span class="info-label">Location Head:</span><span class="info-value">{location_head_name}</span></div>' if location_head_name else ''}
                    {f'<div class="info-item"><span class="info-label">Deputy Head:</span><span class="info-value">{deputy_head_name}</span></div>' if deputy_head_name else ''}
                </div>
                ''' if location_head_name or deputy_head_name else ''}
                
                {f'''
                <div class="info-section">
                    <h2>Business Information</h2>
                    <div class="info-item">
                        <span class="info-label">Company:</span>
                        <span class="info-value">{business_name}</span>
                    </div>
                </div>
                ''' if business_name else ''}
                
                {f'<a href="{maps_url}" class="map-button" target="_blank">📍 View on Google Maps</a>' if maps_url else ''}
            </div>
            
            <div class="footer">
                Scanned from QR Code • Location ID: {location.id}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content
