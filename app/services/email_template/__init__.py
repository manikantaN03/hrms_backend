"""
Email Templates Package
Contains all email templates for the HRMS system
"""

from .mobile_login_template import generate_mobile_login_html, generate_mobile_login_text
from .web_login_template import generate_web_login_html, generate_web_login_text
from .runtime_workman_template import generate_runtime_workman_html, generate_runtime_workman_text
from .birthday_wishes_template import generate_birthday_wishes_html, generate_birthday_wishes_text

__all__ = [
    'generate_mobile_login_html',
    'generate_mobile_login_text',
    'generate_web_login_html',
    'generate_web_login_text',
    'generate_runtime_workman_html',
    'generate_runtime_workman_text',
    'generate_birthday_wishes_html',
    'generate_birthday_wishes_text',
]
