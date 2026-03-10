"""
Birthday Wishes Email Template
Professional animated template for sending birthday wishes to employees
"""

from datetime import datetime
from typing import Dict


def generate_birthday_wishes_html(context: Dict) -> str:
    """
    Generate HTML email for birthday wishes.
    
    Args:
        context: Dictionary containing:
            - employee_name: Employee's full name
            - employee_designation: Employee's designation
            - company_name: Company name
            - sender_name: Name of the person sending wishes (optional)
            - current_year: Current year
            - current_date: Current date formatted
    
    Returns:
        HTML string for email
    """
    sender_name = context.get('sender_name', 'Team')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Happy Birthday!</title>
        <style>
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            @keyframes bounce {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-10px); }}
            }}
            
            @keyframes confetti {{
                0% {{ transform: translateY(-100%) rotate(0deg); opacity: 1; }}
                100% {{ transform: translateY(100vh) rotate(720deg); opacity: 0; }}
            }}
            
            .animate-fade {{ animation: fadeIn 1s ease-out; }}
            .animate-bounce {{ animation: bounce 2s infinite; }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 20px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3); overflow: hidden;">
                        
                        <!-- Header with Balloons -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px 30px; text-align: center; position: relative;">
                                <div style="font-size: 60px; margin-bottom: 10px;">🎉🎂🎈</div>
                                <h1 style="margin: 0; font-size: 42px; font-weight: 700; color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
                                    Happy Birthday!
                                </h1>
                                <div style="font-size: 60px; margin-top: 10px;">🎊🎁🎉</div>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 50px 40px;">
                                
                                <!-- Greeting -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 30px;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 20px 0; font-size: 24px; font-weight: 600; color: #333333; line-height: 1.4;">
                                                Dear {context['employee_name']},
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Birthday Message -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 30px;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 20px 0; font-size: 18px; font-weight: 400; color: #555555; line-height: 1.8;">
                                                Wishing you a very <strong style="color: #f5576c;">Happy Birthday!</strong> 🎉
                                            </p>
                                            <p style="margin: 0 0 20px 0; font-size: 18px; font-weight: 400; color: #555555; line-height: 1.8;">
                                                May this special day bring you happiness, good health, and success in both your personal and professional life. Your dedication and contributions to <strong>{context['company_name']}</strong> are truly appreciated, and we are grateful to have you as a part of our team.
                                            </p>
                                            <p style="margin: 0; font-size: 18px; font-weight: 400; color: #555555; line-height: 1.8;">
                                                May the year ahead be filled with new opportunities, achievements, and memorable moments.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Decorative Birthday Cake -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 40px 0;">
                                    <tr>
                                        <td align="center">
                                            <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 30px; border-radius: 15px; display: inline-block;">
                                                <div style="font-size: 80px; line-height: 1;">🎂</div>
                                                <p style="margin: 15px 0 0 0; font-size: 20px; font-weight: 600; color: #d63031;">
                                                    Enjoy Your Special Day!
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Closing Message -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #f0f0f0;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333333;">
                                                Best wishes,
                                            </p>
                                            <p style="margin: 0 0 5px 0; font-size: 18px; font-weight: 600; color: #667eea;">
                                                {sender_name}
                                            </p>
                                            <p style="margin: 0; font-size: 16px; font-weight: 400; color: #888888;">
                                                {context['company_name']}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                            </td>
                        </tr>
                        
                        <!-- Footer with Confetti -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                                <p style="margin: 0; font-size: 16px; color: #ffffff; font-weight: 500;">
                                    🎈 Celebrate, Smile, and Make Beautiful Memories! 🎈
                                </p>
                                <p style="margin: 15px 0 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.8);">
                                    © {context['current_year']} {context['company_name']}. All rights reserved.
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def generate_birthday_wishes_text(context: Dict) -> str:
    """
    Generate plain text email for birthday wishes.
    
    Args:
        context: Dictionary with employee and company details
    
    Returns:
        Plain text string for email
    """
    sender_name = context.get('sender_name', 'Team')
    
    return f"""
🎉🎂🎈 HAPPY BIRTHDAY! 🎊🎁🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dear {context['employee_name']},

Wishing you a very Happy Birthday! 🎉

May this special day bring you happiness, good health, and success in both 
your personal and professional life. Your dedication and contributions to 
{context['company_name']} are truly appreciated, and we are grateful to 
have you as a part of our team.

May the year ahead be filled with new opportunities, achievements, and 
memorable moments.

🎂 Enjoy Your Special Day! 🎂

Best wishes,
{sender_name}
{context['company_name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎈 Celebrate, Smile, and Make Beautiful Memories! 🎈

© {context['current_year']} {context['company_name']}. All rights reserved.
    """
