"""
Cost to Company (CTC) Email Template
Professional email template for sending CTC reports to employees
"""

from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal


def generate_ctc_email_template(employee_data: Dict[str, Any], company_name: str = "DCM HRMS") -> str:
    """
    Generate professional HTML email template for Cost to Company report
    
    Args:
        employee_data: Dictionary containing employee CTC information
        company_name: Name of the company
    
    Returns:
        HTML string for email body
    """
    
    # Extract employee information
    employee_name = employee_data.get('employee_name', 'Employee')
    employee_code = employee_data.get('employee_code', 'N/A')
    designation = employee_data.get('designation', 'N/A')
    department = employee_data.get('department', 'N/A')
    location = employee_data.get('location', 'N/A')
    
    # Extract salary information
    basic_salary = float(employee_data.get('basic_salary', 0))
    gross_salary = float(employee_data.get('gross_salary', 0))
    total_ctc = float(employee_data.get('total_ctc', 0))
    total_earnings = float(employee_data.get('total_earnings', 0))
    total_deductions = float(employee_data.get('total_deductions', 0))
    total_employer_contributions = float(employee_data.get('total_employer_contributions', 0))
    net_payable = float(employee_data.get('net_payable', 0))
    
    # Extract component breakdowns
    earnings = employee_data.get('earnings', [])
    deductions = employee_data.get('deductions', [])
    employer_contributions = employee_data.get('employer_contributions', [])
    
    # Format date
    current_date = datetime.now().strftime('%B %d, %Y')
    effective_from = employee_data.get('effective_from', 'N/A')
    
    # Generate earnings rows
    earnings_rows = ""
    for earning in earnings:
        component_name = earning.get('component_name', 'N/A')
        amount = float(earning.get('amount', 0))
        earnings_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{component_name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">₹{amount:,.2f}</td>
        </tr>
        """
    
    # Generate deductions rows
    deductions_rows = ""
    for deduction in deductions:
        component_name = deduction.get('component_name', 'N/A')
        amount = float(deduction.get('amount', 0))
        deductions_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{component_name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">₹{amount:,.2f}</td>
        </tr>
        """
    
    # Generate employer contributions rows
    employer_rows = ""
    for contribution in employer_contributions:
        component_name = contribution.get('component_name', 'N/A')
        amount = float(contribution.get('amount', 0))
        employer_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{component_name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">₹{amount:,.2f}</td>
        </tr>
        """
    
    # Build HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cost to Company Report</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">Cost to Company Report</h1>
                                <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 14px; opacity: 0.9;">{company_name}</p>
                            </td>
                        </tr>
                        
                        <!-- Greeting -->
                        <tr>
                            <td style="padding: 30px 30px 20px 30px;">
                                <p style="margin: 0; font-size: 16px; color: #333333; line-height: 1.6;">
                                    Dear <strong>{employee_name}</strong>,
                                </p>
                                <p style="margin: 15px 0 0 0; font-size: 14px; color: #666666; line-height: 1.6;">
                                    Please find below your detailed Cost to Company (CTC) breakdown as of <strong>{current_date}</strong>.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Employee Information -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border-radius: 6px; padding: 20px;">
                                    <tr>
                                        <td style="padding: 8px 0;">
                                            <span style="color: #666666; font-size: 13px;">Employee Code:</span>
                                            <span style="color: #333333; font-size: 14px; font-weight: 600; margin-left: 10px;">{employee_code}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0;">
                                            <span style="color: #666666; font-size: 13px;">Designation:</span>
                                            <span style="color: #333333; font-size: 14px; font-weight: 600; margin-left: 10px;">{designation}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0;">
                                            <span style="color: #666666; font-size: 13px;">Department:</span>
                                            <span style="color: #333333; font-size: 14px; font-weight: 600; margin-left: 10px;">{department}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0;">
                                            <span style="color: #666666; font-size: 13px;">Location:</span>
                                            <span style="color: #333333; font-size: 14px; font-weight: 600; margin-left: 10px;">{location}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0;">
                                            <span style="color: #666666; font-size: 13px;">Effective From:</span>
                                            <span style="color: #333333; font-size: 14px; font-weight: 600; margin-left: 10px;">{effective_from}</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- CTC Summary -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                                    Salary Summary
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden;">
                                    <tr style="background-color: #f8f9fa;">
                                        <td style="padding: 15px; font-weight: 600; color: #333333;">Basic Salary</td>
                                        <td style="padding: 15px; text-align: right; font-weight: 700; color: #667eea; font-size: 16px;">₹{basic_salary:,.2f}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 15px; font-weight: 600; color: #333333; border-top: 1px solid #e0e0e0;">Gross Salary</td>
                                        <td style="padding: 15px; text-align: right; font-weight: 700; color: #667eea; font-size: 16px; border-top: 1px solid #e0e0e0;">₹{gross_salary:,.2f}</td>
                                    </tr>
                                    <tr style="background-color: #667eea;">
                                        <td style="padding: 15px; font-weight: 700; color: #ffffff; font-size: 16px;">Total CTC (Annual)</td>
                                        <td style="padding: 15px; text-align: right; font-weight: 700; color: #ffffff; font-size: 18px;">₹{total_ctc:,.2f}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Earnings Breakdown -->
                        {f'''
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid #28a745; padding-bottom: 10px;">
                                    Earnings Breakdown
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden;">
                                    <thead>
                                        <tr style="background-color: #28a745; color: #ffffff;">
                                            <th style="padding: 12px; text-align: left; font-weight: 600;">Component</th>
                                            <th style="padding: 12px; text-align: right; font-weight: 600;">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {earnings_rows}
                                        <tr style="background-color: #f8f9fa; font-weight: 700;">
                                            <td style="padding: 15px; color: #333333;">Total Earnings</td>
                                            <td style="padding: 15px; text-align: right; color: #28a745; font-size: 16px;">₹{total_earnings:,.2f}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                        ''' if earnings else ''}
                        
                        <!-- Deductions Breakdown -->
                        {f'''
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                                    Deductions Breakdown
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden;">
                                    <thead>
                                        <tr style="background-color: #dc3545; color: #ffffff;">
                                            <th style="padding: 12px; text-align: left; font-weight: 600;">Component</th>
                                            <th style="padding: 12px; text-align: right; font-weight: 600;">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {deductions_rows}
                                        <tr style="background-color: #f8f9fa; font-weight: 700;">
                                            <td style="padding: 15px; color: #333333;">Total Deductions</td>
                                            <td style="padding: 15px; text-align: right; color: #dc3545; font-size: 16px;">₹{total_deductions:,.2f}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                        ''' if deductions else ''}
                        
                        <!-- Employer Contributions -->
                        {f'''
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #333333; border-bottom: 2px solid #17a2b8; padding-bottom: 10px;">
                                    Employer Contributions
                                </h2>
                                <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden;">
                                    <thead>
                                        <tr style="background-color: #17a2b8; color: #ffffff;">
                                            <th style="padding: 12px; text-align: left; font-weight: 600;">Component</th>
                                            <th style="padding: 12px; text-align: right; font-weight: 600;">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {employer_rows}
                                        <tr style="background-color: #f8f9fa; font-weight: 700;">
                                            <td style="padding: 15px; color: #333333;">Total Employer Contributions</td>
                                            <td style="padding: 15px; text-align: right; color: #17a2b8; font-size: 16px;">₹{total_employer_contributions:,.2f}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                        ''' if employer_contributions else ''}
                        
                        <!-- Net Payable -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 6px; padding: 20px;">
                                    <tr>
                                        <td style="color: #ffffff; font-size: 16px; font-weight: 600;">Net Monthly Payable</td>
                                        <td style="color: #ffffff; font-size: 22px; font-weight: 700; text-align: right;">₹{net_payable:,.2f}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer Note -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px;">
                                    <p style="margin: 0; font-size: 13px; color: #856404; line-height: 1.6;">
                                        <strong>Note:</strong> This is a system-generated email. The CTC breakdown is for your reference only. 
                                        For any queries or clarifications, please contact the HR department.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
                                <p style="margin: 0; font-size: 12px; color: #666666;">
                                    © {datetime.now().year} {company_name}. All rights reserved.
                                </p>
                                <p style="margin: 10px 0 0 0; font-size: 11px; color: #999999;">
                                    This email was sent from an automated system. Please do not reply to this email.
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
    
    return html_template


def generate_ctc_plain_text(employee_data: Dict[str, Any], company_name: str = "DCM HRMS") -> str:
    """
    Generate plain text version of CTC email for email clients that don't support HTML
    
    Args:
        employee_data: Dictionary containing employee CTC information
        company_name: Name of the company
    
    Returns:
        Plain text string for email body
    """
    
    employee_name = employee_data.get('employee_name', 'Employee')
    employee_code = employee_data.get('employee_code', 'N/A')
    designation = employee_data.get('designation', 'N/A')
    department = employee_data.get('department', 'N/A')
    total_ctc = float(employee_data.get('total_ctc', 0))
    net_payable = float(employee_data.get('net_payable', 0))
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    plain_text = f"""
Cost to Company Report
{company_name}
{current_date}

Dear {employee_name},

Please find below your Cost to Company (CTC) breakdown:

EMPLOYEE INFORMATION
--------------------
Employee Code: {employee_code}
Designation: {designation}
Department: {department}

SALARY SUMMARY
--------------
Total CTC (Annual): ₹{total_ctc:,.2f}
Net Monthly Payable: ₹{net_payable:,.2f}

For detailed breakdown, please view the HTML version of this email or contact HR department.

Note: This is a system-generated email. For any queries, please contact the HR department.

© {datetime.now().year} {company_name}. All rights reserved.
    """
    
    return plain_text.strip()
