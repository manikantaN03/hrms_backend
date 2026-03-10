# Email Templates

This directory contains all email templates for the Levitica HRMS system.

## Structure

All email templates follow a consistent structure:
- Professional dark theme design matching company branding
- Responsive HTML layout
- Plain text fallback for email clients that don't support HTML
- Company logo and HR contact information
- Clear call-to-action buttons

## Available Templates

### 1. Mobile Login Template (`mobile_login_template.py`)

**Purpose:** Send mobile app login credentials to employees

**Functions:**
- `generate_mobile_login_html(context)` - Generates HTML email
- `generate_mobile_login_text(context)` - Generates plain text email

**Context Parameters:**
```python
{
    "employee_name": str,        # Employee's full name
    "employee_code": str,        # Employee code
    "mobile": str,               # Employee's mobile number
    "company_name": str,         # Company name
    "app_download_link": str,    # Link to download mobile app
    "support_email": str,        # Support email address
    "current_year": int,         # Current year
    "current_date": str          # Current date formatted (e.g., "23 Feb 2025")
}
```

**Email Features:**
- Employee code and mobile number display
- Download app button
- Step-by-step login instructions
- List of mobile app features
- Support contact information

### 2. Web Login Template (`web_login_template.py`)

**Purpose:** Send web portal login credentials to employees

**Functions:**
- `generate_web_login_html(context)` - Generates HTML email
- `generate_web_login_text(context)` - Generates plain text email

**Context Parameters:**
```python
{
    "employee_name": str,        # Employee's full name
    "employee_code": str,        # Employee code
    "email": str,                # Employee's email address
    "company_name": str,         # Company name
    "web_portal_url": str,       # URL to web portal
    "support_email": str,        # Support email address
    "current_year": int,         # Current year
    "current_date": str,         # Current date formatted
    "temporary_password": str    # Optional temporary password
}
```

**Email Features:**
- Employee code and email display
- Optional temporary password section
- Access web portal button
- Login instructions (with/without temporary password)
- Security notice for temporary passwords
- List of web portal features
- Support contact information

### 3. Runtime Workman Template (`runtime_workman_template.py`)

**Purpose:** Send Runtime Workman mobile app login credentials to employees

**Functions:**
- `generate_runtime_workman_html(context)` - Generates HTML email
- `generate_runtime_workman_text(context)` - Generates plain text email

**Context Parameters:**
```python
{
    "employee_name": str,        # Employee's full name
    "company_id": str,           # Company ID (e.g., "LEV001")
    "employee_code": str,        # Employee code (e.g., "LEV040")
    "login_pin": str,            # Login PIN (e.g., "644894")
    "company_name": str,         # Company name
    "support_email": str,        # Support email address
    "current_year": int,         # Current year
    "current_date": str          # Current date formatted
}
```

**Email Features:**
- Runtime HRMS branding with logo
- Dark theme design (#0a0e1a background)
- Company ID, Employee Code, and Login PIN display
- Download Runtime Workman button (Play Store link)
- Runtime Workman Guide link (PDF)
- Step-by-step login instructions
- Security notice
- Feature list

**Links:**
- Play Store: `https://play.google.com/store/apps/details?id=com.runtime.workman`
- User Guide: `https://runtimehrms.com/downloads/runtime-workman-user-guide-2022.pdf`

## Usage

### In Email Service

```python
from app.services.email_template import (
    generate_mobile_login_html,
    generate_mobile_login_text,
    generate_web_login_html,
    generate_web_login_text,
    generate_runtime_workman_html,
    generate_runtime_workman_text
)

# Mobile Login Email
context = {
    "employee_name": "John Doe",
    "employee_code": "EMP001",
    "mobile": "+91 9876543210",
    "company_name": "Levitica Technologies",
    "app_download_link": "https://play.google.com/store/...",
    "support_email": "hr@leviticatechnologies.com",
    "current_year": 2025,
    "current_date": "23 Feb 2025"
}

html_content = generate_mobile_login_html(context)
text_content = generate_mobile_login_text(context)

# Web Login Email
context = {
    "employee_name": "John Doe",
    "employee_code": "EMP001",
    "email": "john.doe@company.com",
    "company_name": "Levitica Technologies",
    "web_portal_url": "https://hrms.leviticatechnologies.com",
    "support_email": "hr@leviticatechnologies.com",
    "current_year": 2025,
    "current_date": "23 Feb 2025",
    "temporary_password": "Temp@123"  # Optional
}

html_content = generate_web_login_html(context)
text_content = generate_web_login_text(context)

# Runtime Workman Email
context = {
    "employee_name": "Nagadurga",
    "company_id": "LEV001",
    "employee_code": "LEV040",
    "login_pin": "644894",
    "company_name": "Levitica Technologies",
    "support_email": "hr@leviticatechnologies.com",
    "current_year": 2025,
    "current_date": "27 Feb 2025"
}

html_content = generate_runtime_workman_html(context)
text_content = generate_runtime_workman_text(context)
```

### In API Endpoints

The email service provides convenient methods:

```python
from app.services.email_service import email_service

# Send mobile login email
await email_service.send_mobile_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    mobile="+91 9876543210",
    company_name="Levitica Technologies"
)

# Send web login email
await email_service.send_web_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    company_name="Levitica Technologies",
    temporary_password=None  # Optional
)

# Send Runtime Workman email
await email_service.send_runtime_workman_email(
    employee_name="Nagadurga",
    company_id="LEV001",
    employee_code="LEV040",
    login_pin="644894",
    employee_email="nagadurga@company.com",
    company_name="Levitica Technologies"
)
```

## Design Guidelines

When creating new email templates:

1. **Consistency:** Follow the existing dark theme design
2. **Branding:** Include company logo and colors
3. **Responsive:** Use table-based layout for email client compatibility
4. **Accessibility:** Provide plain text alternatives
5. **Clear CTAs:** Use prominent buttons for primary actions
6. **Contact Info:** Always include support contact information
7. **Professional Tone:** Maintain formal yet friendly language

## Color Scheme

- Background: `#2b2b2b` (Dark gray)
- Primary: `#4a9eff` (Blue)
- Accent: `#d32f2f` (Red - for logo)
- Text: `#ffffff` (White)
- Secondary Text: `#cccccc` (Light gray)
- Muted Text: `#999999` (Gray)
- Card Background: `#333333` (Medium gray)

## Testing

Before deploying new templates:

1. Test HTML rendering in multiple email clients (Gmail, Outlook, Apple Mail)
2. Verify plain text fallback is readable
3. Check all links are working
4. Ensure responsive design on mobile devices
5. Validate all context variables are properly substituted

## Adding New Templates

1. Create a new file: `{template_name}_template.py`
2. Implement `generate_{template_name}_html(context)` function
3. Implement `generate_{template_name}_text(context)` function
4. Add imports to `__init__.py`
5. Add corresponding method in `email_service.py`
6. Document in this README
7. Test thoroughly before deployment
