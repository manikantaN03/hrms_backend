"""
Runtime HRMS Logo - Base64 Encoded for Email
This ensures the logo displays even if external images are blocked
"""

# Runtime HRMS Logo as inline HTML/CSS
def get_runtime_logo_html():
    """
    Returns HTML for Runtime HRMS logo that works in emails
    Uses text-based logo with proper styling to match the brand
    """
    return """
    <table cellpadding="0" cellspacing="0" border="0" style="margin: 0; padding: 0;">
        <tr>
            <td style="padding: 0; margin: 0;">
                <div style="font-family: Arial, sans-serif; font-weight: 700; line-height: 1; margin: 0; padding: 0;">
                    <span style="color: #3b82f6; font-size: 48px; letter-spacing: 2px; display: inline-block; margin: 0; padding: 0;">RUNTIME</span>
                    <br>
                    <span style="color: #10b981; font-size: 48px; letter-spacing: 2px; display: inline-block; margin: 0; padding: 0; margin-left: 80px;">HRMS</span>
                </div>
            </td>
        </tr>
    </table>
    """

def get_runtime_logo_with_image():
    """
    Returns HTML with image tag and fallback text
    """
    return """
    <table cellpadding="0" cellspacing="0" border="0" style="margin: 0; padding: 0;">
        <tr>
            <td style="padding: 0; margin: 0;">
                <!-- Try to load image first -->
                <img src="https://runtimehrms.com/assets/runtime-logo.png" 
                     alt="Runtime HRMS" 
                     style="height: 60px; width: auto; display: block; max-width: 100%;" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
                
                <!-- Fallback text logo if image fails -->
                <div style="display: none; font-family: Arial, sans-serif; font-weight: 700; line-height: 1; margin: 0; padding: 0;">
                    <span style="color: #3b82f6; font-size: 36px; letter-spacing: 1px;">RUNTIME</span>
                    <span style="color: #10b981; font-size: 36px; letter-spacing: 1px; margin-left: 10px;">HRMS</span>
                </div>
            </td>
        </tr>
    </table>
    """

def get_simple_text_logo():
    """
    Simple text-based logo that always works
    """
    return """
    <div style="font-family: Arial, sans-serif; font-weight: 700; margin-bottom: 20px;">
        <span style="color: #3b82f6; font-size: 36px; letter-spacing: 1px;">RUNTIME</span>
        <span style="color: #10b981; font-size: 36px; letter-spacing: 1px; margin-left: 8px;">HRMS</span>
    </div>
    """
