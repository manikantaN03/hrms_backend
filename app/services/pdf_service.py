"""
PDF Generation Service
Generates PDF documents from offer letters and other content
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor
from io import BytesIO
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF documents"""
    
    def generate_offer_letter_pdf(
        self,
        letter_content: str,
        candidate_name: str,
        company_name: str = "Company"
    ) -> Optional[BytesIO]:
        """
        Generate PDF from offer letter content
        
        Args:
            letter_content: The offer letter text content
            candidate_name: Candidate's name for filename
            company_name: Company name for header
        
        Returns:
            BytesIO object containing the PDF, or None if failed
        """
        try:
            # Create a BytesIO buffer
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=50,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                leading=18,
                textColor=HexColor('#333333'),
                alignment=TA_LEFT,
                fontName='Helvetica'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=13,
                textColor=HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            # Add title
            title = Paragraph(f"<b>Offer Letter</b>", title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # Process letter content - split by lines and preserve formatting
            lines = letter_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    # Add space for empty lines
                    elements.append(Spacer(1, 8))
                    continue
                
                # Escape HTML special characters
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Check if line looks like a heading (all caps or starts with specific keywords)
                is_heading = False
                heading_keywords = ['Subject:', 'EMPLOYMENT DETAILS:', 'COMPENSATION:', 'WORKING HOURS:', 
                                   'TERMS:', 'BENEFITS:', 'Position Details:', 'Salary Details:', 
                                   'Working Conditions:', 'Terms & Conditions:']
                
                for keyword in heading_keywords:
                    if line.startswith(keyword):
                        is_heading = True
                        break
                
                # Apply appropriate style
                if is_heading:
                    para = Paragraph(f"<b>{line}</b>", heading_style)
                else:
                    # Check for bullet points
                    if line.startswith('•') or line.startswith('-'):
                        line = f"&nbsp;&nbsp;&nbsp;&nbsp;{line}"
                    
                    para = Paragraph(line, body_style)
                
                elements.append(para)
            
            # Add footer space
            elements.append(Spacer(1, 30))
            
            # Build PDF
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            buffer.seek(0)
            logger.info(f"Successfully generated PDF for {candidate_name}")
            return buffer
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_filename(self, candidate_name: str, document_type: str = "Offer_Letter") -> str:
        """
        Generate a clean filename for the PDF
        
        Args:
            candidate_name: Candidate's name
            document_type: Type of document
        
        Returns:
            Sanitized filename
        """
        # Remove special characters and spaces
        clean_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_'))
        clean_name = clean_name.replace(' ', '_')
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        
        return f"{document_type}_{clean_name}_{date_str}.pdf"


# Create singleton instance
pdf_service = PDFService()
