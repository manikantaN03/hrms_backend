"""
Web Login Email Template
Template for sending web portal login credentials to employees
"""

from datetime import datetime
from typing import Dict


def generate_web_login_html(context: Dict) -> str:
    """
    Generate HTML email for web login credentials.
    
    Args:
        context: Dictionary containing:
            - employee_name: Employee's full name
            - employee_code: Employee code
            - email: Employee's email address
            - company_name: Company name
            - web_portal_url: URL to web portal
            - support_email: Support email address
            - current_year: Current year
            - current_date: Current date formatted
            - temporary_password: Temporary password (optional)
    
    Returns:
        HTML string for email
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web Portal Login Access</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #1a1a1a;">
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #1a1a1a; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background-color: #2d2d2d; border-radius: 0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">
                        <tr>
                            <td style="padding: 40px 50px;">
                                
                                <!-- Runtime HRMS Logo -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 30px;">
                                    <tr>
                                        <td>
                                            <div style="font-family: Arial, sans-serif; font-weight: 700; line-height: 1.2;">
                                                <span style="color: #3b82f6; font-size: 32px; letter-spacing: 1px;">RUNTIME</span>
                                                <span style="color: #10b981; font-size: 32px; letter-spacing: 1px; margin-left: 8px;">HRMS</span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Horizontal Line -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 35px;">
                                    <tr>
                                        <td style="border-bottom: 1px solid #3a3a3a;"></td>
                                    </tr>
                                </table>
                                
                                <!-- Greeting -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 35px;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 35px 0; font-size: 26px; font-weight: 400; color: #d0d0d0; line-height: 1.3;">
                                                Hello {context['employee_name']} ,
                                            </p>
                                            <p style="margin: 0; font-size: 18px; font-weight: 300; color: #d0d0d0; line-height: 1.5;">
                                                Please note your Web Portal login details:
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Login Credentials -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 35px 0;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 12px 0; font-size: 18px; font-weight: 400; color: #d0d0d0; line-height: 1.6;">
                                                Employee Code: {context['employee_code']}
                                            </p>
                                            <p style="margin: 0{' 0 12px 0' if context.get('temporary_password') else ''}; font-size: 18px; font-weight: 400; color: #d0d0d0; line-height: 1.6;">
                                                Email: {context['email']}
                                            </p>
                                            {f'''<p style="margin: 0; font-size: 18px; font-weight: 400; color: #d0d0d0; line-height: 1.6;">
                                                Temporary Password: {context['temporary_password']}
                                            </p>''' if context.get('temporary_password') else ''}
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Web Portal Link -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 35px 0 40px 0;">
                                    <tr>
                                        <td>
                                            <a href="{context['web_portal_url']}" style="font-size: 18px; font-weight: 400; color: #5ba3e8; text-decoration: none; line-height: 1.6; display: block;">
                                                Access Web Portal
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Team Runtime -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                    <tr>
                                        <td>
                                            <p style="margin: 0; font-size: 18px; font-weight: 400; color: #d0d0d0; line-height: 1.6;">
                                                Team Runtime
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def generate_web_login_text(context: Dict) -> str:
    """
    Generate plain text email for web login credentials.
    
    Args:
        context: Dictionary with employee and company details
    
    Returns:
        Plain text string for email
    """
    return f"""
RUNTIME HRMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hello {context['employee_name']} ,

Please note your Web Portal login details:

Employee Code: {context['employee_code']}
Email: {context['email']}
{f"Temporary Password: {context['temporary_password']}" if context.get('temporary_password') else ''}

Access Web Portal
{context['web_portal_url']}

Team Runtime

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
