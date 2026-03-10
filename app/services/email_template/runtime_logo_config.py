"""
Runtime HRMS Logo Configuration
Provides logo URLs and fallback options for email templates
"""

# Primary logo URL (hosted)
RUNTIME_LOGO_URL = "https://runtimehrms.com/assets/runtime-logo.png"

# Alternative logo URLs (fallbacks)
RUNTIME_LOGO_FALLBACK_URLS = [
    "https://runtimehrms.com/assets/runtime-logo.png",
    "https://cdn.runtimehrms.com/logo.png",
]

# Logo dimensions
RUNTIME_LOGO_HEIGHT = "60px"
RUNTIME_LOGO_WIDTH = "auto"

# Fallback HTML logo (SVG-based text logo)
RUNTIME_LOGO_FALLBACK_HTML = """
<table cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
    <tr>
        <td style="padding-right: 8px; vertical-align: middle;">
            <!-- Runtime Logo Icon (SVG-like) -->
            <svg width="50" height="50" viewBox="0 0 50 50" style="display: block;">
                <defs>
                    <linearGradient id="runtimeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="50" height="50" rx="8" fill="url(#runtimeGradient)"/>
                <path d="M 15 15 L 15 35 L 20 35 L 20 27 L 25 27 L 32 35 L 38 35 L 30 26 Q 35 25 35 20 Q 35 15 30 15 Z M 20 20 L 20 22 L 28 22 Q 30 22 30 20 Q 30 18 28 18 L 20 18 Z" fill="white"/>
            </svg>
        </td>
        <td style="vertical-align: middle;">
            <div style="font-size: 24px; font-weight: 700; color: #2196F3; letter-spacing: 0.5px; line-height: 1;">RUNTIME</div>
            <div style="font-size: 20px; font-weight: 600; color: #4CAF50; letter-spacing: 1px; margin-top: 2px; line-height: 1;">HRMS</div>
        </td>
    </tr>
</table>
"""

# Text-only fallback (for plain text emails)
RUNTIME_LOGO_TEXT = """
╔═══════════════════════════════╗
║   RUNTIME HRMS                ║
╚═══════════════════════════════╝
"""


def get_runtime_logo_html(use_fallback: bool = False) -> str:
    """
    Get Runtime HRMS logo HTML.
    
    Args:
        use_fallback: If True, use HTML/SVG fallback instead of image
    
    Returns:
        HTML string for logo
    """
    if use_fallback:
        return RUNTIME_LOGO_FALLBACK_HTML
    
    return f'''
    <img 
        src="{RUNTIME_LOGO_URL}" 
        alt="Runtime HRMS" 
        style="height: {RUNTIME_LOGO_HEIGHT}; width: {RUNTIME_LOGO_WIDTH}; display: block; margin: 0 auto;"
        onerror="this.onerror=null; this.style.display='none'; this.parentElement.innerHTML='{RUNTIME_LOGO_FALLBACK_HTML.replace("'", "&apos;")}';"
    />
    '''


def get_runtime_logo_text() -> str:
    """Get text-only version of Runtime HRMS logo."""
    return RUNTIME_LOGO_TEXT
