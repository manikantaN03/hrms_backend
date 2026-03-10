"""
HR Management API Endpoints
Complete HR communication, policies, and management API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, get_current_admin
from app.api.v1.endpoints.master_setup import get_user_business_id
from app.models.user import User
from app.models.employee import Employee
from app.models.hrmanagement import (
    Notification, Letter, Alert, Greeting, HRPolicy, PolicyAcknowledgment,
    NotificationRead, AlertAcknowledgment, NotificationStatus, LetterType,
    AlertType, GreetingType, PolicyStatus, NotificationPriority, GreetingConfiguration
)
from app.schemas.hrmanagement import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    LetterCreate, LetterUpdate, LetterResponse,
    AlertCreate, AlertUpdate, AlertResponse,
    GreetingCreate, GreetingUpdate, GreetingResponse,
    GreetingConfigurationCreate, GreetingConfigurationUpdate, GreetingConfigurationResponse,
    GreetingConfigurationSaveRequest, GreetingConfigItem,
    HRPolicyCreate, HRPolicyCreateRequest, HRPolicyUpdate, HRPolicyResponse,
    HRDashboardResponse, HRDashboardStats,
    PolicyAcknowledgmentCreate, PolicyAcknowledgmentResponse,
    AlertAcknowledgmentCreate, AlertAcknowledgmentResponse,
    APIResponse, APIListResponse, APIErrorResponse
)
from app.services.template_service import TemplateService

router = APIRouter()


@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get HR notifications with filtering and pagination - Optimized for Performance
    
    **Returns:**
    - List of notifications in table format
    - Frontend-compatible structure
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Optimized query - avoid complex joins initially
        query = db.query(Notification)
        
        # Apply business filtering for non-superadmin users
        if business_id:
            query = query.filter(Notification.business_id == business_id)
        
        # Apply filters with better error handling
        if status and status.upper() in ['DRAFT', 'PUBLISHED', 'ARCHIVED']:
            query = query.filter(Notification.status == status.upper())
        
        if priority and priority.upper() in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']:
            query = query.filter(Notification.priority == priority.upper())
        
        # Apply pagination with limit to prevent large queries
        offset = (page - 1) * size
        size = min(size, 50)  # Cap at 50 items per page
        notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(size).all()
        
        # Build response with simplified processing
        notification_list = []
        for notif in notifications:
            # Simplified date formatting
            created_date = notif.created_at.strftime('%b %d, %Y') if notif.created_at else "N/A"
            release_date = notif.publish_date.strftime('%b %d, %Y') if notif.publish_date else created_date
            
            # Simplified targeting logic
            sent_to = "All Employees"
            if not notif.target_all_employees:
                if notif.target_departments:
                    sent_to = "Specific Departments"
                elif notif.target_employees:
                    sent_to = "Specific Employees"
                else:
                    sent_to = "Specific Recipients"
            
            notification_data = {
                "id": notif.id,
                "subject": notif.title,
                "releaseDate": release_date,
                "createdOn": f"Created On: {created_date}",
                "content": notif.content,
                "sentTo": sent_to,
                
                # Essential backend fields
                "business_id": notif.business_id,
                "title": notif.title,
                "status": notif.status.value,
                "priority": notif.priority.value,
                "publish_date": notif.publish_date.isoformat() if notif.publish_date else None,
                "expiry_date": notif.expiry_date.isoformat() if notif.expiry_date else None,
                "view_count": notif.view_count or 0,
                "is_pinned": notif.is_pinned,
                "target_all_employees": notif.target_all_employees,
                "target_departments": notif.target_departments,
                "target_employees": notif.target_employees,
                "creator_name": "System",  # Simplified for performance
                "created_at": notif.created_at.isoformat(),
                "updated_at": notif.updated_at.isoformat() if notif.updated_at else None,
                "attachment_url": notif.attachment_url
            }
            notification_list.append(notification_data)
        
        return notification_list
        
    except Exception as e:
        # Log the error for debugging
        print(f"Notifications endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch notifications: {str(e)}"
        )


@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new HR notification
    
    **Creates:**
    - Company-wide or targeted notifications
    - Announcement and communication system
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no business_id, get the first business (for superadmin)
        if not business_id:
            from app.models.business import Business
            first_business = db.query(Business).first()
            if first_business:
                business_id = first_business.id
        
        # If no employee_id, get the first employee (for superadmin)
        if not employee_id:
            from app.models.employee import Employee
            first_employee = db.query(Employee).first()
            if first_employee:
                employee_id = first_employee.id
        
        # Create notification
        new_notification = Notification(
            business_id=business_id,
            created_by=employee_id,
            title=notification_data.title,
            content=notification_data.content,
            priority=notification_data.priority,
            publish_date=notification_data.publish_date,
            expiry_date=notification_data.expiry_date,
            target_all_employees=notification_data.target_all_employees,
            target_departments=notification_data.target_departments,
            target_employees=notification_data.target_employees,
            is_pinned=notification_data.is_pinned,
            attachment_url=notification_data.attachment_url,
            status=NotificationStatus.PUBLISHED if notification_data.publish_date else NotificationStatus.DRAFT
        )
        
        db.add(new_notification)
        db.commit()
        
        return NotificationResponse.from_orm(new_notification)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )


@router.get("/letters/debug", response_model=Dict[str, Any])
async def debug_letters(
    db: Session = Depends(get_db)
):
    """Debug endpoint to check all letters in database"""
    try:
        from sqlalchemy import text
        
        # Get all letters with basic info
        result = db.execute(text("""
            SELECT id, business_id, employee_id, letter_type, subject, 
                   created_at, updated_at 
            FROM hr_letters 
            ORDER BY created_at DESC 
            LIMIT 20
        """))
        
        letters = []
        for row in result:
            letters.append({
                "id": row[0],
                "business_id": row[1],
                "employee_id": row[2],
                "letter_type": row[3],
                "subject": row[4],
                "created_at": str(row[5]),
                "updated_at": str(row[6]) if row[6] else None
            })
        
        return {
            "total_letters": len(letters),
            "letters": letters,
            "message": "Debug info retrieved successfully"
        }
        
    except Exception as e:
        return {
            "error": f"Debug failed: {str(e)}",
            "total_letters": 0,
            "letters": []
        }


@router.get("/letters/test-db", response_model=Dict[str, Any])
async def test_database_connection(
    db: Session = Depends(get_db)
):
    """Test database connection and table structure"""
    try:
        from sqlalchemy import text
        
        # Test 1: Check if hr_letters table exists
        result = db.execute(text("SELECT COUNT(*) FROM hr_letters"))
        letter_count = result.scalar()
        
        # Test 2: Check if we can insert a simple record
        test_sql = text("""
            INSERT INTO hr_letters (
                business_id, employee_id, created_by, letter_type, letter_number,
                subject, content, letter_date, letterhead_used,
                is_generated, is_sent, created_at, updated_at
            ) VALUES (
                1, 1, 1, 'APPOINTMENT', 'TEST-001',
                'Test Letter', 'Test content', CURRENT_DATE, true,
                false, false, NOW(), NOW()
            ) RETURNING id
        """)
        
        result = db.execute(test_sql)
        test_id = result.scalar()
        
        # Test 3: Delete the test record
        delete_sql = text("DELETE FROM hr_letters WHERE id = :test_id")
        db.execute(delete_sql, {"test_id": test_id})
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Database connection and table structure are working",
            "existing_letters": letter_count,
            "test_insert_id": test_id
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database test failed: {str(e)}",
            "error_type": type(e).__name__
        }


@router.get("/letters", response_model=List[Dict[str, Any]])
async def get_letters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    letter_type: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get HR letters with filtering and pagination - Frontend Compatible Format
    
    **Returns:**
    - List of generated letters in table format
    - Frontend-compatible structure
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Base query - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Letter).options(
            joinedload(Letter.employee),
            joinedload(Letter.creator)
        )
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        # Apply filters
        if letter_type:
            try:
                letter_type_enum = LetterType(letter_type)
                query = query.filter(Letter.letter_type == letter_type_enum)
            except ValueError:
                pass  # Invalid letter type, ignore filter
        
        if employee_id:
            query = query.filter(Letter.employee_id == employee_id)
        
        # Apply pagination
        offset = (page - 1) * size
        letters = query.order_by(desc(Letter.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        letter_list = []
        for letter in letters:
            # Format last updated date
            last_updated = letter.updated_at or letter.created_at
            last_updated_formatted = last_updated.strftime('%b %d, %Y') if last_updated else "N/A"
            
            # Create description based on letter type and employee
            employee_name = f"{letter.employee.first_name} {letter.employee.last_name}" if letter.employee else "Unknown Employee"
            description = f"{letter.letter_type.value.replace('_', ' ').title()} letter for {employee_name}"
            
            letter_data = {
                "id": letter.id,
                "name": letter.subject,
                "description": description,
                "lastUpdated": last_updated_formatted,
                
                # Additional fields for backend compatibility
                "business_id": letter.business_id,
                "employee_id": letter.employee_id,
                "created_by": letter.created_by,
                "letter_type": letter.letter_type.value,
                "letter_number": letter.letter_number,
                "subject": letter.subject,
                "content": letter.content,
                "letter_date": letter.letter_date.isoformat(),
                "effective_date": letter.effective_date.isoformat() if letter.effective_date else None,
                "is_generated": letter.is_generated,
                "is_sent": letter.is_sent,
                "sent_date": letter.sent_date.isoformat() if letter.sent_date else None,
                "is_digitally_signed": letter.is_digitally_signed,
                "signed_by": letter.signed_by,
                "signature_date": letter.signature_date.isoformat() if letter.signature_date else None,
                "template_id": letter.template_id,
                "letterhead_used": letter.letterhead_used,
                "pdf_url": letter.pdf_url,
                "employee_name": employee_name,
                "employee_code": letter.employee.employee_code if letter.employee else None,
                "creator_name": f"{letter.creator.first_name} {letter.creator.last_name}" if letter.creator else None,
                "created_at": letter.created_at.isoformat(),
                "updated_at": letter.updated_at.isoformat() if letter.updated_at else None
            }
            letter_list.append(letter_data)
        
        return letter_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch letters: {str(e)}"
        )


@router.post("/letters", response_model=Dict[str, Any])
async def create_letter(
    letter_data: LetterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new HR letter with business isolation"""
    try:
        from sqlalchemy import text
        from datetime import date
        import time
        
        # Get user's business_id and employee_id
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id, get first employee from user's business
        if not employee_id:
            from app.models.employee import Employee
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id
            ).first()
            if first_employee:
                employee_id = first_employee.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No employees found in your business"
                )
        
        # Validate employee belongs to user's business
        if letter_data.employee_id:
            from app.models.employee import Employee
            employee = db.query(Employee).filter(
                Employee.id == letter_data.employee_id,
                Employee.business_id == business_id
            ).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found or does not belong to your business"
                )
            employee_id = letter_data.employee_id
        
        # Generate unique letter number
        letter_number = f"LTR-{int(time.time())}"
        
        # Use direct SQL to insert the letter with proper business isolation
        sql = text("""
            INSERT INTO hr_letters (
                business_id, employee_id, created_by, letter_type, letter_number,
                subject, content, letter_date, effective_date, letterhead_used,
                is_generated, is_sent, is_digitally_signed, created_at, updated_at
            ) VALUES (
                :business_id, :employee_id, :created_by, :letter_type, :letter_number,
                :subject, :content, :letter_date, :effective_date, true,
                false, false, false, NOW(), NOW()
            ) RETURNING id, letter_number, subject
        """)
        
        # Execute the SQL with proper business isolation
        result = db.execute(sql, {
            'business_id': business_id,
            'employee_id': employee_id,
            'created_by': current_user.id,
            'letter_type': letter_data.letter_type.value,
            'letter_number': letter_number,
            'subject': letter_data.subject[:500],  # Truncate to avoid length issues
            'content': letter_data.content,
            'letter_date': letter_data.letter_date.isoformat() if letter_data.letter_date else date.today().isoformat(),
            'effective_date': letter_data.effective_date.isoformat() if letter_data.effective_date else None
        })
        
        # Commit the transaction
        db.commit()
        
        # Get the result
        row = result.fetchone()
        
        print(f"✅ Letter created with ID: {row[0]}, business_id: {business_id}")
        
        return {
            "id": row[0],
            "letter_number": row[1],
            "subject": row[2],
            "business_id": business_id,
            "message": "Letter created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Raise proper HTTP exceptions instead of returning error dictionaries
        error_msg = str(e)
        print(f"❌ Letter creation error: {error_msg}")
        
        if "foreign key" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint error - please ensure employees and businesses exist"
            )
        elif "duplicate" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate letter number - please try again"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create letter: {error_msg}"
            )


@router.get("/letters/{letter_id}", response_model=Dict[str, Any])
async def get_letter(
    letter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get a specific letter by ID - Fixed for superadmin access
    
    **Returns:**
    - Letter details
    - Employee information
    - Generation status
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get letter - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Letter).options(
            joinedload(Letter.employee),
            joinedload(Letter.creator)
        ).filter(Letter.id == letter_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        letter = query.first()
        
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        # Format response
        letter_data = {
            "id": letter.id,
            "business_id": letter.business_id,
            "employee_id": letter.employee_id,
            "created_by": letter.created_by,
            "letter_type": letter.letter_type.value,
            "letter_number": letter.letter_number,
            "subject": letter.subject,
            "content": letter.content,
            "letter_date": letter.letter_date.isoformat(),
            "effective_date": letter.effective_date.isoformat() if letter.effective_date else None,
            "is_generated": letter.is_generated,
            "is_sent": letter.is_sent,
            "sent_date": letter.sent_date.isoformat() if letter.sent_date else None,
            "is_digitally_signed": letter.is_digitally_signed,
            "signed_by": letter.signed_by,
            "signature_date": letter.signature_date.isoformat() if letter.signature_date else None,
            "template_id": letter.template_id,
            "letterhead_used": letter.letterhead_used,
            "pdf_url": letter.pdf_url,
            "employee_name": f"{letter.employee.first_name} {letter.employee.last_name}" if letter.employee else None,
            "employee_code": letter.employee.employee_code if letter.employee else None,
            "creator_name": f"{letter.creator.first_name} {letter.creator.last_name}" if letter.creator else None,
            "created_at": letter.created_at.isoformat(),
            "updated_at": letter.updated_at.isoformat() if letter.updated_at else None
        }
        
        return letter_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch letter: {str(e)}"
        )


@router.put("/letters/{letter_id}", response_model=Dict[str, Any])
async def update_letter(
    letter_id: int,
    letter_data: LetterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a letter with business isolation"""
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get letter with business isolation
        query = db.query(Letter).filter(Letter.id == letter_id)
        
        # Filter by business_id for non-superadmin users
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        letter = query.first()
        
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found or does not belong to your business"
            )
        
        # Update only the fields that are provided
        if letter_data.subject is not None:
            letter.subject = letter_data.subject
        if letter_data.content is not None:
            letter.content = letter_data.content
        if letter_data.effective_date is not None:
            letter.effective_date = letter_data.effective_date
        
        # Force update timestamp
        letter.updated_at = datetime.now()
        
        # Commit changes
        db.commit()
        
        return {
            "success": True,
            "message": "Letter updated successfully",
            "id": letter.id,
            "subject": letter.subject,
            "content": letter.content[:100] + "..." if len(letter.content) > 100 else letter.content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/letters/{letter_id}", response_model=Dict[str, Any])
async def delete_letter(
    letter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a letter - Fixed for superadmin access
    
    **Deletes:**
    - Letter record
    - Associated files
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get letter - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Letter).filter(Letter.id == letter_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        letter = query.first()
        
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        # Delete letter
        db.delete(letter)
        db.commit()
        
        return {
            "message": "Letter deleted successfully",
            "letter_id": letter_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete letter: {str(e)}"
        )


@router.post("/letters/{letter_id}/generate", response_model=Dict[str, Any])
async def generate_letter(
    letter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Generate a letter by processing dynamic field codes - Fixed for superadmin access
    
    **Processes:**
    - Dynamic field codes in letter content
    - Employee and business data replacement
    - Marks letter as generated
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get letter - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Letter).filter(Letter.id == letter_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        letter = query.first()
        
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        # Initialize template service
        template_service = TemplateService(db)
        
        # Use the letter's business_id for template processing
        letter_business_id = letter.business_id
        
        # Process template content
        processed_subject = template_service.process_template(
            letter.subject,
            letter.employee_id,
            letter_business_id,
            letter.letter_date
        )
        
        processed_content = template_service.process_template(
            letter.content,
            letter.employee_id,
            letter_business_id,
            letter.letter_date
        )
        
        # Update letter with processed content
        letter.subject = processed_subject
        letter.content = processed_content
        letter.is_generated = True
        letter.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "message": "Letter generated successfully",
            "letter_id": letter_id,
            "processed_subject": processed_subject,
            "processed_content": processed_content[:200] + "..." if len(processed_content) > 200 else processed_content,
            "is_generated": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate letter: {str(e)}"
        )


@router.post("/letters/{letter_id}/preview", response_model=Dict[str, Any])
async def preview_letter(
    letter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Preview how a letter will look with dynamic field codes processed - Fixed for superadmin access
    
    **Returns:**
    - Original template content
    - Processed preview with actual values
    - Available field codes
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get letter - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Letter).filter(Letter.id == letter_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Letter.business_id == business_id)
        
        letter = query.first()
        
        if not letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        # Initialize template service
        template_service = TemplateService(db)
        
        # Use the letter's business_id for template processing
        letter_business_id = letter.business_id
        
        # Get preview for subject and content
        subject_preview = template_service.preview_template(
            letter.subject,
            letter.employee_id,
            letter_business_id,
            letter.letter_date
        )
        
        content_preview = template_service.preview_template(
            letter.content,
            letter.employee_id,
            letter_business_id,
            letter.letter_date
        )
        
        return {
            "letter_id": letter_id,
            "subject": {
                "original": subject_preview['original_template'],
                "preview": subject_preview['processed_preview']
            },
            "content": {
                "original": content_preview['original_template'],
                "preview": content_preview['processed_preview']
            },
            "available_fields": template_service.get_available_fields(),
            "is_generated": letter.is_generated
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview letter: {str(e)}"
        )


@router.get("/letters/fields/available", response_model=Dict[str, Any])
async def get_available_fields(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available dynamic field codes
    
    **Returns:**
    - Available field codes with descriptions
    - Usage examples
    """
    try:
        template_service = TemplateService(db)
        available_fields = template_service.get_available_fields()
        
        return {
            "available_fields": available_fields,
            "usage_example": "Use {employee_name} in your template to insert the employee's full name",
            "field_count": len(available_fields),
            "syntax": "Use curly braces around field names: {field_name}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available fields: {str(e)}"
        )


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    alert_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get HR alerts with filtering and pagination - Frontend Compatible Format
    
    **Returns:**
    - List of alerts in table format
    - Frontend-compatible structure
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Base query
        query = db.query(Alert).options(
            joinedload(Alert.creator)
        )
        
        if business_id:
            query = query.filter(Alert.business_id == business_id)
        
        # Apply filters
        if alert_type:
            try:
                alert_type_enum = AlertType(alert_type)
                query = query.filter(Alert.alert_type == alert_type_enum)
            except ValueError:
                pass  # Invalid alert type, ignore filter
        
        if is_active is not None:
            query = query.filter(Alert.is_active == is_active)
        
        # Apply pagination
        offset = (page - 1) * size
        alerts = query.order_by(desc(Alert.alert_date)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        alert_list = []
        for alert in alerts:
            # Generate alert description based on attendance settings
            alert_description = ""
            if alert.condition and alert.days and alert.send_letter:
                alert_description = f"If {alert.condition} is more than {alert.days} day(s), send {alert.send_letter}"
            else:
                # Fallback to general message
                alert_description = alert.message[:100] + "..." if len(alert.message) > 100 else alert.message
            
            alert_data = {
                "id": alert.id,
                "alertName": alert.alert_name or alert.title,
                "alertDescription": alert_description,
                "status": "Active" if alert.is_active else "Inactive",
                
                # Frontend form fields
                "condition": alert.condition or "",
                "days": alert.days or 1,
                "sendLetter": alert.send_letter or "",
                "checkEvery": alert.check_every or "day",
                "active": alert.is_active,
                
                # Additional backend fields for compatibility
                "business_id": alert.business_id,
                "created_by": alert.created_by,
                "alert_type": alert.alert_type.value,
                "title": alert.title,
                "message": alert.message,
                "alert_date": alert.alert_date.isoformat(),
                "expiry_date": alert.expiry_date.isoformat() if alert.expiry_date else None,
                "is_popup": alert.is_popup,
                "is_email": alert.is_email,
                "is_sms": alert.is_sms,
                "acknowledgment_required": alert.acknowledgment_required,
                "target_all_employees": alert.target_all_employees,
                "target_departments": alert.target_departments,
                "target_employees": alert.target_employees,
                "creator_name": f"{alert.creator.first_name} {alert.creator.last_name}" if alert.creator else None,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
            }
            alert_list.append(alert_data)
        
        return alert_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}"
        )


@router.post("/alerts", response_model=APIResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new HR alert with business isolation"""
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id, get first employee from user's business
        if not employee_id:
            from app.models.employee import Employee
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id
            ).first()
            if first_employee:
                employee_id = first_employee.id
            else:
                employee_id = current_user.id  # Fallback to user ID
        
        # Use direct SQL to bypass enum validation issues
        from sqlalchemy import text
        
        # Insert alert directly with SQL using correct UPPERCASE enum value
        sql = text("""
            INSERT INTO hr_alerts (
                business_id, created_by, alert_type, title, message, alert_date,
                is_popup, is_email, is_sms, target_all_employees, 
                acknowledgment_required, is_active, alert_name, condition, 
                days, send_letter, check_every, created_at, updated_at
            ) VALUES (
                :business_id, :created_by, 'GENERAL', :title, :message, NOW(),
                :is_popup, :is_email, :is_sms, :target_all_employees,
                :acknowledgment_required, :is_active, :alert_name, :condition,
                :days, :send_letter, :check_every, NOW(), NOW()
            ) RETURNING id, alert_name, title, message, is_active
        """)
        
        result = db.execute(sql, {
            'business_id': business_id,
            'created_by': employee_id,
            'title': alert_data.title,
            'message': alert_data.message,
            'is_popup': alert_data.is_popup,
            'is_email': alert_data.is_email,
            'is_sms': alert_data.is_sms,
            'target_all_employees': alert_data.target_all_employees,
            'acknowledgment_required': alert_data.acknowledgment_required,
            'is_active': alert_data.is_active,
            'alert_name': alert_data.alert_name,
            'condition': alert_data.condition,
            'days': alert_data.days,
            'send_letter': alert_data.send_letter,
            'check_every': alert_data.check_every
        })
        
        db.commit()
        
        # Get the result
        row = result.fetchone()
        
        return APIResponse(
            success=True,
            message="Alert created successfully",
            data={
                "alert": {
                    "id": row[0],
                    "alert_name": row[1],
                    "title": row[2],
                    "message": row[3],
                    "is_active": row[4],
                    "business_id": business_id,
                    "created_at": datetime.now().isoformat()
                }
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=Dict[str, Any])
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific alert by ID - Fixed to handle superadmin access
    
    **Returns:**
    - Alert details
    - Creator information
    - Attendance settings
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get alert - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Alert).options(
            joinedload(Alert.creator)
        ).filter(Alert.id == alert_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Alert.business_id == business_id)
        
        alert = query.first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Generate alert description
        alert_description = ""
        if alert.condition and alert.days and alert.send_letter:
            alert_description = f"If {alert.condition} is more than {alert.days} day(s), send {alert.send_letter}"
        else:
            alert_description = alert.message
        
        # Format response
        alert_data = {
            "id": alert.id,
            "alertName": alert.alert_name or alert.title,
            "alertDescription": alert_description,
            "status": "Active" if alert.is_active else "Inactive",
            "condition": alert.condition or "",
            "days": alert.days or 1,
            "sendLetter": alert.send_letter or "",
            "checkEvery": alert.check_every or "day",
            "active": alert.is_active,
            "business_id": alert.business_id,
            "created_by": alert.created_by,
            "alert_type": alert.alert_type.value,
            "title": alert.title,
            "message": alert.message,
            "alert_date": alert.alert_date.isoformat(),
            "expiry_date": alert.expiry_date.isoformat() if alert.expiry_date else None,
            "is_popup": alert.is_popup,
            "is_email": alert.is_email,
            "is_sms": alert.is_sms,
            "acknowledgment_required": alert.acknowledgment_required,
            "target_all_employees": alert.target_all_employees,
            "creator_name": f"{alert.creator.first_name} {alert.creator.last_name}" if alert.creator else None,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None
        }
        
        return alert_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alert: {str(e)}"
        )


@router.put("/alerts/{alert_id}", response_model=APIResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an alert with business isolation"""
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get alert with business isolation
        query = db.query(Alert).filter(Alert.id == alert_id)
        
        # Filter by business_id for non-superadmin users
        if business_id:
            query = query.filter(Alert.business_id == business_id)
        
        alert = query.first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or does not belong to your business"
            )
        
        # Store original values
        original_name = alert.alert_name or alert.title
        
        # Update only the fields that are provided
        update_data = alert_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        # Force update timestamp
        alert.updated_at = datetime.now()
        
        # Commit changes
        db.commit()
        
        return APIResponse(
            success=True,
            message="Alert updated successfully",
            data={
                "id": alert.id,
                "alert_name": alert.alert_name or alert.title,
                "is_active": alert.is_active,
                "updated_at": alert.updated_at.isoformat(),
                "original_name": original_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/alerts/{alert_id}", response_model=APIResponse)
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete an alert - Fixed to handle superadmin access
    
    **Deletes:**
    - Alert record
    - Associated acknowledgments
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get alert - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(Alert).filter(Alert.id == alert_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(Alert.business_id == business_id)
        
        alert = query.first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Store alert info before deletion
        alert_name = alert.alert_name or alert.title
        
        # Delete associated acknowledgments
        db.query(AlertAcknowledgment).filter(
            AlertAcknowledgment.alert_id == alert_id
        ).delete()
        
        # Delete alert
        db.delete(alert)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Alert deleted successfully",
            data={
                "alert_id": alert_id,
                "alert_name": alert_name,
                "deleted_at": datetime.now().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}"
        )


@router.get("/greetings", response_model=Dict[str, Any])
async def get_greetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get HR greetings configuration - Frontend Compatible Format - Fixed for superadmin access
    
    **Returns:**
    - Greeting configuration settings for Birthday, Work Anniversary, Wedding Anniversary
    - Frontend-compatible structure
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get greeting configurations - handle superadmin access
        query = db.query(GreetingConfiguration)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(GreetingConfiguration.business_id == business_id)
        
        configurations = query.all()
        
        # Separate configurations by type and subtype
        config_map = {}
        for config in configurations:
            if config.greeting_type.value == "birthday":
                config_map["birthday"] = config
            elif config.greeting_type.value == "anniversary":
                # Differentiate between work and wedding anniversary by email subject
                if config.email_subject and "WEDDING_ANNIVERSARY" in config.email_subject:
                    config_map["wedding_anniversary"] = config
                else:
                    config_map["anniversary"] = config
        
        # Default configurations for each greeting type
        default_configs = {
            "birthday": {
                "enabled": True,
                "managerCopy": True,
                "orgFeed": True,
                "subject": "",
                "message": "Happy Birthday, {{first_name}} {{last_name}}! Wishing you a joyful year ahead filled with success and happiness. 🎉"
            },
            "anniversary": {  # Work Anniversary
                "enabled": False,
                "managerCopy": True,
                "orgFeed": True,
                "subject": "",
                "message": ""
            },
            "wedding_anniversary": {
                "enabled": False,
                "managerCopy": True,
                "orgFeed": True,
                "subject": "",
                "message": ""
            }
        }
        
        # Build response with actual configurations or defaults
        response_data = {}
        
        for greeting_type, default_config in default_configs.items():
            if greeting_type in config_map:
                config = config_map[greeting_type]
                # Clean up the email subject for display
                display_subject = config.email_subject or ""
                if display_subject.startswith("WORK_ANNIVERSARY_DEFAULT"):
                    display_subject = ""
                elif display_subject.startswith("WEDDING_ANNIVERSARY_DEFAULT"):
                    display_subject = ""
                
                response_data[greeting_type] = {
                    "id": config.id,
                    "enabled": config.is_enabled,
                    "managerCopy": config.send_to_managers,
                    "orgFeed": config.post_on_org_feed,
                    "subject": display_subject,
                    "message": config.message_template,
                    "processTime": config.process_time,
                    "sendEmail": config.send_email,
                    "sendPushNotification": config.send_push_notification,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat() if config.updated_at else None
                }
            else:
                response_data[greeting_type] = default_config
        
        return {
            "configurations": response_data,
            "instructions": {
                "processing_time": "Greetings are processed between 7AM to 8AM every morning",
                "dynamic_fields": [
                    {"field": "{{first_name}}", "description": "Employee's first name"},
                    {"field": "{{last_name}}", "description": "Employee's last name"}
                ],
                "delivery_methods": [
                    "Email notifications to employees/managers",
                    "Push notifications on mobile app (if registered)",
                    "Organization feed posts (if enabled)"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch greeting configurations: {str(e)}"
        )


@router.post("/greetings/save", response_model=APIResponse)
async def save_greetings_configuration(
    configurations: GreetingConfigurationSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Save HR greetings configuration with business isolation
    
    **Saves:**
    - Birthday greeting settings
    - Work anniversary greeting settings  
    - Wedding anniversary greeting settings
    
    **Request Body:**
    - At least one greeting configuration (birthday, workAnniversary, or weddingAnniversary) is required
    - Each configuration must have enabled status and message template
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id, get first employee from user's business
        if not employee_id:
            from app.models.employee import Employee
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id
            ).first()
            if first_employee:
                employee_id = first_employee.id
            else:
                employee_id = current_user.id  # Fallback to user ID
        
        # Mapping of frontend keys to greeting types and identifiers
        type_mapping = {
            "birthday": ("birthday", GreetingType.BIRTHDAY),
            "workAnniversary": ("work_anniversary", GreetingType.ANNIVERSARY),
            "weddingAnniversary": ("wedding_anniversary", GreetingType.ANNIVERSARY)
        }
        
        saved_configs = {}
        
        # Convert Pydantic model to dict for processing
        config_dict = configurations.dict(exclude_none=True)
        
        for config_key, config_data in config_dict.items():
            if config_key not in type_mapping or config_data is None:
                continue
                
            subtype, greeting_type = type_mapping[config_key]
            
            # For anniversary types, we'll store them with different email subjects to differentiate
            # This is a workaround since we can't easily add a subtype field
            email_subject = config_data.get("subject", "")
            if config_key == "workAnniversary" and not email_subject:
                email_subject = "WORK_ANNIVERSARY_DEFAULT"
            elif config_key == "weddingAnniversary" and not email_subject:
                email_subject = "WEDDING_ANNIVERSARY_DEFAULT"
            
            # Check if configuration already exists - use email_subject as differentiator for anniversaries
            query = db.query(GreetingConfiguration).filter(
                GreetingConfiguration.business_id == business_id,
                GreetingConfiguration.greeting_type == greeting_type
            )
            
            if greeting_type == GreetingType.ANNIVERSARY:
                # For anniversaries, differentiate by email subject prefix
                if config_key == "workAnniversary":
                    query = query.filter(
                        or_(
                            GreetingConfiguration.email_subject.like("WORK_ANNIVERSARY_%"),
                            GreetingConfiguration.email_subject == ""
                        )
                    )
                elif config_key == "weddingAnniversary":
                    query = query.filter(
                        GreetingConfiguration.email_subject.like("WEDDING_ANNIVERSARY_%")
                    )
            
            existing_config = query.first()
            
            if existing_config:
                # Update existing configuration
                existing_config.is_enabled = config_data.get("enabled", True)
                existing_config.send_to_managers = config_data.get("managerCopy", True)
                existing_config.post_on_org_feed = config_data.get("orgFeed", True)
                existing_config.email_subject = email_subject
                existing_config.message_template = config_data.get("message", "Happy greetings!")
                existing_config.updated_at = datetime.now()
                
                saved_configs[config_key] = {
                    "id": existing_config.id,
                    "action": "updated"
                }
            else:
                # Create new configuration
                new_config = GreetingConfiguration(
                    business_id=business_id,
                    created_by=employee_id,
                    greeting_type=greeting_type,
                    is_enabled=config_data.get("enabled", True),
                    send_to_managers=config_data.get("managerCopy", True),
                    post_on_org_feed=config_data.get("orgFeed", True),
                    email_subject=email_subject,
                    message_template=config_data.get("message", "Happy greetings!")
                )
                
                db.add(new_config)
                db.flush()  # Get the ID
                
                saved_configs[config_key] = {
                    "id": new_config.id,
                    "action": "created"
                }
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="Greetings configuration saved successfully",
            data={
                "saved_configurations": saved_configs,
                "total_configs": len(saved_configs),
                "business_id": business_id
            }
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save greetings configuration: {str(e)}"
        )


@router.post("/greetings", response_model=GreetingResponse)
async def create_greeting(
    greeting_data: GreetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new HR greeting
    
    **Creates:**
    - Birthday and anniversary wishes
    - Festival greetings
    - Achievement celebrations
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Create greeting
        new_greeting = Greeting(
            business_id=business_id,
            employee_id=greeting_data.employee_id,
            created_by=employee_id,
            greeting_type=greeting_data.greeting_type,
            title=greeting_data.title,
            message=greeting_data.message,
            greeting_date=greeting_data.greeting_date,
            display_from=greeting_data.display_from,
            display_until=greeting_data.display_until,
            image_url=greeting_data.image_url,
            video_url=greeting_data.video_url,
            is_public=greeting_data.is_public,
            show_on_dashboard=greeting_data.show_on_dashboard,
            send_notification=greeting_data.send_notification
        )
        
        db.add(new_greeting)
        db.commit()
        
        return GreetingResponse.from_orm(new_greeting)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create greeting: {str(e)}"
        )


@router.get("/hrpolicies", response_model=List[Dict[str, Any]])
async def get_hr_policies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get HR policies with filtering and pagination - Frontend Compatible Format - Fixed for superadmin access
    
    **Returns:**
    - List of company policies in table format
    - Frontend-compatible structure
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Base query
        query = db.query(HRPolicy).options(
            joinedload(HRPolicy.creator),
            joinedload(HRPolicy.approver)
        )
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(HRPolicy.business_id == business_id)
        
        # Apply filters
        if category:
            query = query.filter(HRPolicy.category == category)
        
        if status:
            try:
                status_enum = PolicyStatus(status)
                query = query.filter(HRPolicy.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        # Apply pagination
        offset = (page - 1) * size
        policies = query.order_by(desc(HRPolicy.created_at)).offset(offset).limit(size).all()
        
        # Build response in frontend-compatible format
        policy_list = []
        for policy in policies:
            # Format dates
            created_date = policy.created_at.strftime('%m/%d/%Y') if policy.created_at else "N/A"
            updated_date = policy.updated_at.strftime('%m/%d/%Y') if policy.updated_at else created_date
            
            policy_data = {
                "id": policy.id,
                "name": policy.policy_name,  # Frontend expects 'name'
                "type": policy.category,     # Frontend expects 'type' 
                "createdOn": created_date,   # Frontend expects 'createdOn'
                "updatedOn": updated_date,   # Frontend expects 'updatedOn'
                
                # Additional fields for backend compatibility
                "policy_name": policy.policy_name,
                "policy_code": policy.policy_code,
                "category": policy.category,
                "description": policy.description,
                "version": policy.version,
                "status": policy.status.value,
                "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                "review_date": policy.review_date.isoformat() if policy.review_date else None,
                "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
                "is_mandatory_reading": policy.is_mandatory_reading,
                "acknowledgment_required": policy.acknowledgment_required,
                "applies_to_all": policy.applies_to_all,
                "creator_name": f"{policy.creator.first_name} {policy.creator.last_name}" if policy.creator else None,
                "approver_name": f"{policy.approver.first_name} {policy.approver.last_name}" if policy.approver else None,
                "approval_date": policy.approval_date.isoformat() if policy.approval_date else None,
                "created_at": policy.created_at.isoformat(),
                "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
                "document_url": policy.document_url,
                "content": policy.content,
                "file": None,  # For frontend compatibility
                "fileUrl": policy.document_url  # For frontend compatibility
            }
            policy_list.append(policy_data)
        
        return policy_list
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HR policies: {str(e)}"
        )


@router.post("/hrpolicies", response_model=APIResponse)
async def create_hr_policy(
    policy_data: HRPolicyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new HR policy with business isolation
    
    **Creates:**
    - Company policies and procedures
    - Policy documentation
    - Compliance management
    
    **Request Body:**
    - policyName: Required, name of the policy
    - policyType: Required, either 'online' or 'upload'
    - policyBody: Required for online policies
    - policyFile: Required for upload policies
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # If no employee_id, get first employee from user's business
        if not employee_id:
            from app.models.employee import Employee
            first_employee = db.query(Employee).filter(
                Employee.business_id == business_id
            ).first()
            if first_employee:
                employee_id = first_employee.id
            else:
                employee_id = current_user.id  # Fallback to user ID
        
        # Extract data from validated Pydantic model
        policy_name = policy_data.policyName.strip()
        policy_type = policy_data.policyType
        policy_body = policy_data.policyBody
        policy_file = policy_data.policyFile
        category = policy_data.type or "General"
        
        # Generate policy code
        policy_count = db.query(HRPolicy).filter(HRPolicy.business_id == business_id).count()
        policy_code = f"POL-{datetime.now().year}-{policy_count + 1:04d}"
        
        # For upload policies, set content to a placeholder if no body provided
        content = policy_body if policy_body else f"Policy document: {policy_file}" if policy_type == "upload" else ""
        
        # Create policy
        new_policy = HRPolicy(
            business_id=business_id,
            created_by=employee_id,
            policy_name=policy_name,
            policy_code=policy_code,
            category=category,
            description=f"Policy created via {policy_type} method",
            content=content,
            version="1.0",
            status=PolicyStatus.ACTIVE,
            effective_date=date.today(),
            is_mandatory_reading=False,
            acknowledgment_required=False,
            applies_to_all=True,
            document_url=policy_file if policy_type == "upload" else None
        )
        
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
        
        # Return frontend-compatible response
        return APIResponse(
            success=True,
            message="Policy created successfully",
            data={
                "policy": {
                    "id": new_policy.id,
                    "name": new_policy.policy_name,
                    "type": new_policy.category,
                    "createdOn": new_policy.created_at.strftime('%m/%d/%Y'),
                    "status": new_policy.status.value,
                    "policyCode": new_policy.policy_code,
                    "version": new_policy.version,
                    "effectiveDate": new_policy.effective_date.isoformat() if new_policy.effective_date else None,
                    "documentUrl": new_policy.document_url
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create HR policy: {str(e)}"
        )


@router.delete("/hrpolicies/{policy_id}", response_model=APIResponse)
async def delete_hr_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete an HR policy
    
    **Deletes:**
    - Policy record
    - Associated files
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get policy - handle superadmin access (no business_id filtering for superadmin)
        query = db.query(HRPolicy).filter(HRPolicy.id == policy_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(HRPolicy.business_id == business_id)
        
        policy = query.first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        # Store policy info before deletion
        policy_name = policy.policy_name
        policy_code = policy.policy_code
        
        # Delete policy acknowledgments first
        db.query(PolicyAcknowledgment).filter(
            PolicyAcknowledgment.policy_id == policy_id
        ).delete()
        
        # Delete policy
        db.delete(policy)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Policy deleted successfully",
            data={
                "policy_id": policy_id,
                "policy_name": policy_name,
                "policy_code": policy_code,
                "deleted_at": datetime.now().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete policy: {str(e)}"
        )


@router.get("/hrpolicies/{policy_id}/download", response_model=Dict[str, Any])
async def download_hr_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and download HR policy document
    
    **Returns:**
    - Policy document URL or content for download
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get policy - handle superadmin access
        query = db.query(HRPolicy).filter(HRPolicy.id == policy_id)
        
        # Only filter by business_id if user has one (not superadmin)
        if business_id:
            query = query.filter(HRPolicy.business_id == business_id)
        
        policy = query.first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        # If policy has a document URL, return it
        if policy.document_url:
            return {
                "download_url": policy.document_url,
                "filename": f"{policy.policy_name}.pdf",
                "type": "file"
            }
        
        # For online policies, generate downloadable content
        policy_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{policy.policy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .policy-title {{ font-size: 24px; font-weight: bold; color: #333; }}
                .policy-info {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
                .content {{ margin-top: 30px; }}
                .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="policy-title">{policy.policy_name}</div>
                <div>Policy Code: {policy.policy_code or 'N/A'}</div>
            </div>
            
            <div class="policy-info">
                <strong>Category:</strong> {policy.category}<br>
                <strong>Version:</strong> {policy.version}<br>
                <strong>Status:</strong> {policy.status.value}<br>
                <strong>Effective Date:</strong> {policy.effective_date.strftime('%B %d, %Y') if policy.effective_date else 'N/A'}<br>
                {f'<strong>Description:</strong> {policy.description}<br>' if policy.description else ''}
            </div>
            
            <div class="content">
                {policy.content}
            </div>
            
            <div class="footer">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
                This document is for internal use only.
            </div>
        </body>
        </html>
        """
        
        return {
            "download_content": policy_html,
            "filename": f"{policy.policy_name.replace(' ', '_')}.html",
            "type": "content",
            "policy_name": policy.policy_name,
            "policy_code": policy.policy_code
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate policy download: {str(e)}"
        )


# MISSING NOTIFICATION ENDPOINTS
@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific notification by ID
    
    **Returns:**
    - Notification details
    - Creator information
    - Read status
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get notification
        notification = db.query(Notification).options(
            joinedload(Notification.creator)
        ).filter(
            Notification.id == notification_id,
            Notification.business_id == business_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Increment view count
        notification.view_count += 1
        db.commit()
        
        return NotificationResponse.from_orm(notification)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notification: {str(e)}"
        )


@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a notification
    
    **Updates:**
    - Notification content and settings
    - Publishing status
    - Targeting options
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get notification
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.business_id == business_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Update fields
        update_data = notification_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(notification, field, value)
        
        notification.updated_at = datetime.now()
        db.commit()
        
        return NotificationResponse.from_orm(notification)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )


@router.delete("/notifications/{notification_id}", response_model=APIResponse)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a notification
    
    **Deletes:**
    - Notification record
    - Associated read tracking
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Get notification with optional business_id filter
        query = db.query(Notification).filter(Notification.id == notification_id)
        if business_id:
            query = query.filter(Notification.business_id == business_id)
        
        notification = query.first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Store notification info before deletion
        notification_title = notification.title
        
        # Delete associated read records
        db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id
        ).delete()
        
        # Delete notification
        db.delete(notification)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Notification deleted successfully",
            data={
                "notification_id": notification_id,
                "notification_title": notification_title,
                "deleted_at": datetime.now().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )


@router.get("/notifications/employees/search", response_model=List[Dict[str, Any]])
async def search_employees_for_notifications(
    q: str = Query("", min_length=0, description="Search query - empty returns all employees"),
    limit: int = Query(100, ge=1, le=200, description="Maximum results - increased for all employees"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search employees for notification targeting - Enhanced to show all 98 employees
    
    **Returns:**
    - List of employees matching search criteria
    - If no search query, returns all active employees
    - Increased limit to accommodate all employees
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Base query for employees with optimized joins
        from app.models.employee import Employee
        from app.models.department import Department
        from app.models.designations import Designation
        
        query = db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation)
        ).filter(Employee.is_active == True)
        
        # For superadmin (no business_id), show all employees
        # For regular users, filter by business_id
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Apply search filter only if search query is provided
        if q and len(q.strip()) > 0:
            search_filter = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_filter),
                    Employee.last_name.ilike(search_filter),
                    Employee.employee_code.ilike(search_filter),
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_filter),
                    Employee.email.ilike(search_filter)
                )
            )
        
        # Order by name for consistent results
        query = query.order_by(Employee.first_name, Employee.last_name)
        
        # Get employees with increased limit
        employees = query.limit(limit).all()
        
        # Build response with optimized queries
        employee_list = []
        for emp in employees:
            # Use joined data when available, fallback to individual queries
            dept_name = "N/A"
            designation_name = "N/A"
            
            try:
                # Try to use joined data first
                if hasattr(emp, 'department') and emp.department:
                    dept_name = emp.department.name
                elif emp.department_id:
                    dept = db.query(Department).filter(Department.id == emp.department_id).first()
                    if dept:
                        dept_name = dept.name
                        
                if hasattr(emp, 'designation') and emp.designation:
                    designation_name = emp.designation.name
                elif emp.designation_id:
                    designation = db.query(Designation).filter(Designation.id == emp.designation_id).first()
                    if designation:
                        designation_name = designation.name
            except Exception as dept_error:
                print(f"Department/Designation lookup error for employee {emp.id}: {dept_error}")
                pass  # Use defaults if queries fail
            
            employee_data = {
                "id": emp.id,
                "first_name": emp.first_name or "",
                "last_name": emp.last_name or "",
                "employee_code": emp.employee_code or "",
                "department_name": dept_name,
                "designation_name": designation_name,
                "email": emp.email or "",
                "is_active": emp.is_active,
                "business_id": emp.business_id
            }
            employee_list.append(employee_data)
        
        print(f"Employee search: query='{q}', found={len(employee_list)} employees")
        return employee_list
        
    except Exception as e:
        print(f"Employee search error: {str(e)}")
        # Return empty list on error instead of raising exception
        return []


@router.get("/notifications/employees/all", response_model=List[Dict[str, Any]])
async def get_all_employees_for_notifications(
    limit: int = Query(200, ge=1, le=500, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all employees for notification targeting - No search required
    
    **Returns:**
    - List of all active employees
    - Useful for dropdown population and browsing all 98 employees
    """
    try:
        business_id = get_user_business_id(current_user, db)
        
        # Base query for all active employees
        from app.models.employee import Employee
        from app.models.department import Department
        from app.models.designations import Designation
        
        query = db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.designation)
        ).filter(Employee.is_active == True)
        
        # For superadmin (no business_id), show all employees
        # For regular users, filter by business_id
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Order by name for consistent results
        query = query.order_by(Employee.first_name, Employee.last_name)
        
        # Get all employees
        employees = query.limit(limit).all()
        
        # Build response
        employee_list = []
        for emp in employees:
            # Use joined data when available
            dept_name = "N/A"
            designation_name = "N/A"
            
            try:
                if hasattr(emp, 'department') and emp.department:
                    dept_name = emp.department.name
                elif emp.department_id:
                    dept = db.query(Department).filter(Department.id == emp.department_id).first()
                    if dept:
                        dept_name = dept.name
                        
                if hasattr(emp, 'designation') and emp.designation:
                    designation_name = emp.designation.name
                elif emp.designation_id:
                    designation = db.query(Designation).filter(Designation.id == emp.designation_id).first()
                    if designation:
                        designation_name = designation.name
            except Exception as dept_error:
                print(f"Department/Designation lookup error for employee {emp.id}: {dept_error}")
                pass
            
            employee_data = {
                "id": emp.id,
                "first_name": emp.first_name or "",
                "last_name": emp.last_name or "",
                "employee_code": emp.employee_code or "",
                "department_name": dept_name,
                "designation_name": designation_name,
                "email": emp.email or "",
                "is_active": emp.is_active,
                "business_id": emp.business_id
            }
            employee_list.append(employee_data)
        
        print(f"All employees: found={len(employee_list)} active employees")
        return employee_list
        
    except Exception as e:
        print(f"Get all employees error: {str(e)}")
        return []


@router.get("/employees/direct", response_model=List[Dict[str, Any]])
async def get_employees_direct(
    limit: int = Query(100, ge=1, le=200, description="Maximum results"),
    search: str = Query("", description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Direct employee access with business isolation - SECURED
    
    **Returns:**
    - List of active employees from user's business only
    - Requires authentication
    """
    try:
        business_id = get_user_business_id(current_user, db)
        print(f"Direct employee endpoint called: search='{search}', limit={limit}, business_id={business_id}")
        
        # Simple query without complex joins - WITH BUSINESS ISOLATION
        query = db.query(Employee).filter(Employee.is_active == True)
        
        # CRITICAL: Filter by business_id
        if business_id:
            query = query.filter(Employee.business_id == business_id)
        
        # Apply search filter if provided
        if search and search.strip():
            search_filter = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_filter),
                    Employee.last_name.ilike(search_filter),
                    Employee.employee_code.ilike(search_filter)
                )
            )
        
        # Order and limit
        employees = query.order_by(Employee.first_name).limit(limit).all()
        
        print(f"Found {len(employees)} employees in business {business_id}")
        
        # Build simple response
        employee_list = []
        for emp in employees:
            employee_data = {
                "id": emp.id,
                "first_name": emp.first_name or "",
                "last_name": emp.last_name or "",
                "full_name": f"{emp.first_name or ''} {emp.last_name or ''}".strip(),
                "employee_code": emp.employee_code or "",
                "department_name": "Department",  # Simplified for now
                "designation_name": "Designation",  # Simplified for now
                "email": emp.email or "",
                "is_active": emp.is_active,
                "business_id": emp.business_id
            }
            employee_list.append(employee_data)
        
        print(f"Returning {len(employee_list)} employees for business {business_id}")
        return employee_list
        
    except Exception as e:
        print(f"Direct employee query error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search employees: {str(e)}"
        )


@router.post("/notifications/{notification_id}/read", response_model=APIResponse)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read
    
    **Creates:**
    - Read tracking record
    - User engagement data
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Check if notification exists
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.business_id == business_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check if already read
        existing_read = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id,
            NotificationRead.employee_id == employee_id
        ).first()
        
        if existing_read:
            return APIResponse(
                success=True,
                message="Notification already marked as read",
                data={
                    "notification_id": notification_id,
                    "read_date": existing_read.read_date.isoformat(),
                    "already_read": True
                }
            )
        
        # Create read record
        read_record = NotificationRead(
            notification_id=notification_id,
            employee_id=employee_id,
            read_date=datetime.now()
        )
        
        db.add(read_record)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Notification marked as read",
            data={
                "notification_id": notification_id,
                "read_date": read_record.read_date.isoformat(),
                "already_read": False
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.get("/notifications/center/list", response_model=Dict[str, Any])
async def get_notification_center_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for notification center
    
    **Returns:**
    - User-specific notifications
    - Read status
    - Formatted for notification center UI
    """
    try:
        business_id = get_user_business_id(current_user, db)
        employee_id = getattr(current_user, 'employee_id', None)
        
        # Base query for published notifications
        query = db.query(Notification).options(
            joinedload(Notification.creator)
        ).filter(
            Notification.business_id == business_id,
            Notification.status == NotificationStatus.PUBLISHED
        )
        
        # Filter by publish date (only show current notifications)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        query = query.filter(
            or_(
                Notification.publish_date.is_(None),
                Notification.publish_date <= now
            )
        ).filter(
            or_(
                Notification.expiry_date.is_(None),
                Notification.expiry_date > now
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(size).all()
        
        # Build notification center format
        notification_list = []
        for notif in notifications:
            # Check if read by current user
            read_record = db.query(NotificationRead).filter(
                NotificationRead.notification_id == notif.id,
                NotificationRead.employee_id == employee_id
            ).first()
            
            # Calculate relative time
            time_diff = datetime.now(timezone.utc) - notif.created_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} d"
                if time_diff.seconds // 3600 > 0:
                    time_str += f" {time_diff.seconds // 3600} h"
            elif time_diff.seconds // 3600 > 0:
                time_str = f"{time_diff.seconds // 3600} h"
                if (time_diff.seconds % 3600) // 60 > 0:
                    time_str += f" {(time_diff.seconds % 3600) // 60} m"
            else:
                time_str = f"{time_diff.seconds // 60} m"
            
            # Determine color based on priority
            color_map = {
                "low": "#6b7280",
                "medium": "#f59e0b", 
                "high": "#2563eb",
                "urgent": "#dc2626"
            }
            
            notification_data = {
                "id": notif.id,
                "text": notif.title,
                "time": time_str,
                "color": color_map.get(notif.priority.value, "#f59e0b"),
                "reason": notif.content[:200] + "..." if len(notif.content) > 200 else notif.content,
                "type": notif.priority.value,
                "is_read": read_record is not None,
                "is_pinned": notif.is_pinned,
                "creator_name": f"{notif.creator.first_name} {notif.creator.last_name}" if notif.creator else None,
                "created_at": notif.created_at.isoformat(),
                "attachment_url": notif.attachment_url
            }
            notification_list.append(notification_data)
        
        return {
            "notifications": notification_list,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "unread_count": len([n for n in notification_list if not n["is_read"]])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notification center list: {str(e)}"
        )