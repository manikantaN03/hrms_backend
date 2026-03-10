# Quick Start Guide - Employee Login Email Templates

## For Developers

### 1. Send Mobile Login Email

```python
from app.services.email_service import email_service

# Basic usage
success = await email_service.send_mobile_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    mobile="+91 9876543210"
)

# With custom company name
success = await email_service.send_mobile_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    mobile="+91 9876543210",
    company_name="My Company"
)
```

### 2. Send Web Login Email

```python
from app.services.email_service import email_service

# OTP-based login (no password)
success = await email_service.send_web_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com"
)

# With temporary password
success = await email_service.send_web_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    temporary_password="Temp@123"
)

# With custom company name
success = await email_service.send_web_login_email(
    employee_name="John Doe",
    employee_code="EMP001",
    employee_email="john.doe@company.com",
    company_name="My Company"
)
```

### 3. Use in API Endpoints

The endpoints are already implemented and ready to use:

```python
# POST /api/v1/allemployees/{employee_id}/access/send-mobile-login
# POST /api/v1/allemployees/{employee_id}/access/send-web-login
```

---

## For Frontend Developers

### 1. Send Mobile Login

```javascript
async function sendMobileLogin(employeeId) {
  try {
    const response = await fetch(
      `/api/v1/allemployees/${employeeId}/access/send-mobile-login`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Mobile login email sent successfully');
      showSuccessMessage(data.message);
    } else {
      showErrorMessage('Failed to send mobile login email');
    }
  } catch (error) {
    console.error('Error:', error);
    showErrorMessage('An error occurred');
  }
}
```

### 2. Send Web Login

```javascript
async function sendWebLogin(employeeId) {
  try {
    const response = await fetch(
      `/api/v1/allemployees/${employeeId}/access/send-web-login`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Web login email sent successfully');
      showSuccessMessage(data.message);
    } else {
      showErrorMessage('Failed to send web login email');
    }
  } catch (error) {
    console.error('Error:', error);
    showErrorMessage('An error occurred');
  }
}
```

### 3. React Example

```jsx
import { useState } from 'react';

function EmployeeAccessActions({ employeeId }) {
  const [loading, setLoading] = useState(false);
  
  const handleSendMobileLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/allemployees/${employeeId}/access/send-mobile-login`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
      } else {
        toast.error('Failed to send mobile login email');
      }
    } catch (error) {
      toast.error('An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSendWebLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/allemployees/${employeeId}/access/send-web-login`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
      } else {
        toast.error('Failed to send web login email');
      }
    } catch (error) {
      toast.error('An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button 
        onClick={handleSendMobileLogin}
        disabled={loading}
      >
        Send Mobile Login
      </button>
      
      <button 
        onClick={handleSendWebLogin}
        disabled={loading}
      >
        Send Web Login
      </button>
    </div>
  );
}
```

---

## Testing

### 1. Test Email Sending

```python
# In Python shell or test file
import asyncio
from app.services.email_service import email_service

async def test_emails():
    # Test mobile login email
    mobile_success = await email_service.send_mobile_login_email(
        employee_name="Test User",
        employee_code="TEST001",
        employee_email="test@example.com",
        mobile="+91 9876543210"
    )
    print(f"Mobile login email: {'✓ Sent' if mobile_success else '✗ Failed'}")
    
    # Test web login email
    web_success = await email_service.send_web_login_email(
        employee_name="Test User",
        employee_code="TEST001",
        employee_email="test@example.com"
    )
    print(f"Web login email: {'✓ Sent' if web_success else '✗ Failed'}")

# Run test
asyncio.run(test_emails())
```

### 2. Test API Endpoints

```bash
# Test mobile login endpoint
curl -X POST \
  http://localhost:8000/api/v1/allemployees/1/access/send-mobile-login \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Test web login endpoint
curl -X POST \
  http://localhost:8000/api/v1/allemployees/1/access/send-web-login \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Troubleshooting

### Email Not Sending

1. **Check SMTP Configuration**
   ```python
   from app.core.config import settings
   
   print(f"SMTP Host: {settings.SMTP_HOST}")
   print(f"SMTP Port: {settings.SMTP_PORT}")
   print(f"SMTP Username: {settings.SMTP_USERNAME}")
   print(f"SMTP Configured: {settings.is_smtp_configured()}")
   ```

2. **Check Employee Data**
   - Ensure employee has email address
   - For mobile login, ensure employee has mobile number
   - Verify employee exists in database

3. **Check Logs**
   ```bash
   # Look for email-related errors in logs
   tail -f logs/app.log | grep -i email
   ```

### Common Errors

#### "Employee does not have an email address"
- **Solution:** Add email to employee profile

#### "Employee does not have a mobile number"
- **Solution:** Add mobile number to employee profile (for mobile login)

#### "Failed to send email. Please check SMTP configuration."
- **Solution:** Verify SMTP settings in `.env` file
- Check SMTP credentials are correct
- Ensure SMTP server is accessible

#### "SMTP authentication failed"
- **Solution:** Verify SMTP username and password
- Check if 2FA is enabled on email account
- Use app-specific password if required

---

## Configuration

### Environment Variables

Required SMTP settings in `.env`:

```env
SMTP_HOST=mail.leviticatechnologies.com
SMTP_PORT=465
SMTP_USE_TLS=True
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@company.com
SMTP_FROM_NAME=Company HR System
FRONTEND_URL=http://localhost:3000
```

### Customization

#### Change Mobile App Download Link

Edit `app/services/email_service.py`:

```python
async def send_mobile_login_email(...):
    context = {
        ...
        "app_download_link": "YOUR_APP_STORE_LINK",
        ...
    }
```

#### Change Email Templates

Edit template files:
- `app/services/email_template/mobile_login_template.py`
- `app/services/email_template/web_login_template.py`

---

## Best Practices

1. **Always validate employee data** before sending emails
2. **Log email sending attempts** for audit trail
3. **Handle errors gracefully** and provide user feedback
4. **Test in development** before deploying to production
5. **Monitor email delivery** rates and failures
6. **Keep templates updated** with current branding
7. **Provide plain text fallback** for all HTML emails

---

## Support

For issues or questions:
- Check the main README: `app/services/email_template/README.md`
- Review implementation summary: `IMPLEMENTATION_SUMMARY.md`
- Contact: Development Team
