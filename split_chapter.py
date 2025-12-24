#!/usr/bin/env python3
"""
Chapter Splitter - Automatically split chapter documents into sub-topic PDFs

This program takes a chapter document (PDF or plain text) and splits it into
multiple PDFs based on detected sub-topics using heading patterns.

Author: Auto-generated
License: MIT
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY


class SubTopic:
    """Represents a detected sub-topic with its title and content."""
    
    def __init__(self, number: int, title: str, content: str, start_pos: int, heading_number: str = None):
        self.number = number  # Sequential number (1, 2, 3...)
        self.heading_number = heading_number or str(number)  # Original heading number (1.1, 2.1, etc.)
        self.title = title.strip()
        self.content = content.strip()
        self.start_pos = start_pos
    
    def __repr__(self):
        return f"SubTopic({self.heading_number}, '{self.title[:30]}...', {len(self.content)} chars)"


class ChapterSplitter:
    """Main class for splitting chapters into sub-topic PDFs."""
    
    # Regex patterns for detecting sub-topics (hierarchical)
    HEADING_PATTERNS = [
        # Hierarchical numbered headings: 1.1, 1.2, 2.1, etc. (PRIORITY)
        r'^(\d+\.\d+(?:\.\d+)?)\s+([A-Z][^\n]{3,100})$',
        # Top-level numbered headings: 1 Title, 2 Title (without period after number)
        r'^(\d+)\s+([A-Z][^\n]{3,100})$',
        # Traditional numbered: 1. Title, 2. Title
        r'^(\d+)\.\s+([A-Z][^\n]{3,100})$',
        # Roman numerals: I. Title, II. Title, etc.
        r'^([IVX]+)\.\s+([A-Z][^\n]{3,100})$',
        # Alphabetic: A. Title, B. Title, etc.
        r'^([A-Z])\.\s+([A-Z][^\n]{3,100})$',
        # All caps titles (at least 3 words)
        r'^([A-Z][A-Z\s]{10,100})$',
        # Title Case headings (multiple capitalized words)
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,10})$',
    ]
    
    def __init__(self, input_file: str, output_dir: str = "output_subtopics"):
        """
        Initialize the ChapterSplitter.
        
        Args:
            input_file: Path to input PDF or TXT file
            output_dir: Directory to store output PDFs
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.chapter_name = self.input_file.stem
        self.file_extension = self.input_file.suffix.lower()
        
        # Validate input file
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if self.file_extension not in ['.pdf', '.txt']:
            raise ValueError(f"Unsupported file format: {self.file_extension}. Use .pdf or .txt")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_text_from_pdf(self) -> str:
        """
        Extract text from PDF file using available library with improved layout handling.
        
        Returns:
            Extracted text as string
        """
        text = ""
        
        # Try pdfplumber first (better text extraction with layout preservation)
        if pdfplumber:
            try:
                with pdfplumber.open(self.input_file) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        # Extract with layout preservation for better multi-column handling
                        page_text = page.extract_text(
                            layout=True,  # Preserve spatial layout
                            x_tolerance=3,  # Horizontal tolerance for grouping
                            y_tolerance=3   # Vertical tolerance for grouping
                        )
                        if page_text:
                            # Add page marker for debugging
                            text += f"\n--- Page {page_num} ---\n"
                            text += page_text + "\n"
                return text
            except Exception as e:
                print(f"Warning: pdfplumber failed ({e}), trying PyMuPDF...")
        
        # Fallback to PyMuPDF with better text extraction
        if fitz:
            try:
                doc = fitz.open(self.input_file)
                for page_num, page in enumerate(doc, 1):
                    text += f"\n--- Page {page_num} ---\n"
                    # Use "text" mode for better plain text extraction
                    text += page.get_text("text") + "\n"
                doc.close()
                return text
            except Exception as e:
                raise RuntimeError(f"Failed to extract text from PDF: {e}")
        
        raise RuntimeError("No PDF library available. Install pdfplumber or PyMuPDF.")
    
    def extract_text_from_txt(self) -> str:
        """
        Extract text from plain text file.
        
        Returns:
            File content as string
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(self.input_file, 'r', encoding='latin-1') as f:
                return f.read()
    
    def extract_text(self) -> str:
        """
        Extract text from input file based on file type.
        
        Returns:
            Extracted text
        """
        if self.file_extension == '.pdf':
            return self.extract_text_from_pdf()
        else:
            return self.extract_text_from_txt()
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and unwanted patterns.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove page markers added during extraction
        text = re.sub(r'\n---\s*Page\s+\d+\s*---\n', '\n', text)
        
        # Remove reprint dates (e.g., "Reprint 2025-26")
        text = re.sub(r'Reprint\s+\d{4}-\d{2}', '', text)
        
        # Remove multiple blank lines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def save_extracted_text(self, text: str):
        """
        Save extracted text to file for debugging and verification.
        
        Args:
            text: Extracted text to save
        """
        debug_file = self.output_dir / f"{self.chapter_name}_extracted.txt"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"   💾 Saved extracted text to: {debug_file.name}")
        except Exception as e:
            print(f"   ⚠️  Could not save debug file: {e}")
    
    def is_valid_heading(self, heading: str, content: str) -> bool:
        """
        Validate if a detected heading is actually a valid sub-topic.
        
        Args:
            heading: The detected heading text
            content: The content associated with this heading
            
        Returns:
            True if valid, False if should be filtered out
        """
        # Must have minimum content (100 chars to avoid empty sections)
        if len(content) < 100:
            return False
        
        # Heading must have at least 2 words (filters single words like "World")
        words = heading.split()
        if len(words) < 2:
            return False
        
        # Heading must not be too long (likely a sentence, not a heading)
        if len(heading) > 120:
            return False
        
        # Must contain at least one alphabetic character
        if not any(c.isalpha() for c in heading):
            return False
        
        # Filter out common gibberish patterns
        # All caps with many spaces (map labels like "GUINEA    SOMALILAND")
        if re.match(r'^[A-Z\s]{15,}$', heading):
            return False
        
        # Multiple random short words (map labels like "Aleppo Bukhara Wall")
        if len(words) >= 3 and all(len(w) < 8 for w in words):
            # Check if it looks like a list of place names
            if not any(char.isdigit() for char in heading):  # No numbers
                return False
        
        return True
    
    def detect_subtopics(self, text: str) -> List[SubTopic]:
        """
        Detect sub-topics in the text using heading patterns.
        
        Args:
            text: Cleaned chapter text
            
        Returns:
            List of SubTopic objects
        """
        lines = text.split('\n')
        subtopics = []
        potential_headings = []
        
        # First pass: identify potential headings
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped or len(line_stripped) < 3:
                continue
            
            # Check against all heading patterns
            for pattern in self.HEADING_PATTERNS:
                match = re.match(pattern, line_stripped, re.MULTILINE)
                if match:
                    # Store line index, matched heading, and heading number
                    heading_text = match.group(0)
                    # Extract heading number from first capture group
                    heading_number = match.group(1) if match.lastindex >= 1 else None
                    potential_headings.append((i, heading_text, heading_number))
                    break
        
        if not potential_headings:
            raise ValueError("No sub-topics detected in the document. Try a different file or check formatting.")
        
        # Second pass: extract content between headings
        for idx, (line_num, heading, heading_number) in enumerate(potential_headings):
            # Determine content range
            start_line = line_num + 1
            
            if idx < len(potential_headings) - 1:
                end_line = potential_headings[idx + 1][0]
            else:
                end_line = len(lines)
            
            # Extract content
            content_lines = lines[start_line:end_line]
            content = '\n'.join(content_lines).strip()
            
            # Validate heading before creating SubTopic
            if not self.is_valid_heading(heading, content):
                print(f"   🚫 Skipped: '{heading[:50]}...' ({len(content)} chars)")
                continue
            
            # Create SubTopic object
            subtopic = SubTopic(
                number=idx + 1,
                title=heading,
                content=content,
                start_pos=line_num,
                heading_number=heading_number
            )
            
            # Warn if content is suspiciously small (but passed validation)
            if len(content) < 200:
                print(f"   ⚠️  WARNING: [{heading_number}] '{heading[:40]}...' has minimal content ({len(content)} chars)")
            
            subtopics.append(subtopic)
        
        return subtopics
    
    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize text for use in filename.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Safe filename string
        """
        # Remove or replace invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with underscores
        text = re.sub(r'\s+', '_', text)
        # Limit length
        text = text[:50]
        return text
    
    def create_pdf(self, subtopic: SubTopic) -> str:
        """
        Create a PDF file for a single sub-topic.
        
        Args:
            subtopic: SubTopic object
            
        Returns:
            Path to created PDF file
        """
        # Generate filename using hierarchical heading number
        safe_title = self.sanitize_filename(subtopic.title)
        # Use heading_number for better organization (e.g., 1.1, 2.1)
        safe_heading_num = subtopic.heading_number.replace('.', '_')
        filename = f"{self.chapter_name}_{safe_heading_num}_{safe_title}.pdf"
        output_path = self.output_dir / filename
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='#1a1a1a',
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Custom body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            fontName='Helvetica'
        )
        
        # Build PDF content
        story = []
        
        # Add title
        title_para = Paragraph(subtopic.title, title_style)
        story.append(title_para)
        story.append(Spacer(1, 0.3*inch))
        
        # Add content paragraphs
        paragraphs = subtopic.content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                # Escape special characters for reportlab
                para_text = para_text.replace('&', '&amp;')
                para_text = para_text.replace('<', '&lt;')
                para_text = para_text.replace('>', '&gt;')
                
                # Replace single newlines with spaces, preserve paragraph breaks
                para_text = para_text.replace('\n', ' ')
                
                para = Paragraph(para_text, body_style)
                story.append(para)
                story.append(Spacer(1, 0.15*inch))
        
        # Page number callback function
        def add_page_number(canvas, doc):
            """Add page number to bottom center of each page."""
            page_num = canvas.getPageNumber()
            text = f"Page {page_num}"
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawCentredString(
                4.25*inch,  # Center of letter page (8.5" / 2)
                0.5*inch,   # Bottom margin
                text
            )
            canvas.restoreState()
        
        # Build PDF with page numbers
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        return str(output_path)
    
    def process(self) -> List[str]:
        """
        Main processing method: extract, detect, and generate PDFs.
        
        Returns:
            List of generated PDF file paths
        """
        print(f"📖 Processing: {self.input_file.name}")
        print(f"📁 Output directory: {self.output_dir}")
        print()
        
        # Step 1: Extract text
        print("🔍 Extracting text...")
        raw_text = self.extract_text()
        
        if not raw_text or len(raw_text) < 100:
            raise ValueError("Extracted text is too short or empty. File may be corrupted.")
        
        print(f"   ✓ Extracted {len(raw_text)} characters")
        
        # Save extracted text for debugging
        self.save_extracted_text(raw_text)
        
        # Step 2: Clean text
        print("🧹 Cleaning text...")
        cleaned_text = self.clean_text(raw_text)
        print(f"   ✓ Cleaned to {len(cleaned_text)} characters")
        
        # Step 3: Detect sub-topics
        print("🎯 Detecting sub-topics...")
        subtopics = self.detect_subtopics(cleaned_text)
        print(f"   ✓ Found {len(subtopics)} sub-topics")
        print()
        
        # Show detected headings for verification
        print("📋 Detected headings:")
        for subtopic in subtopics:
            content_preview = f"({len(subtopic.content)} chars)"
            print(f"   [{subtopic.heading_number}] {subtopic.title[:60]}... {content_preview}")
        print()
        
        # Step 4: Generate PDFs
        print("📄 Generating PDFs...")
        generated_files = []
        
        for subtopic in subtopics:
            print(f"   [{subtopic.heading_number}] {subtopic.title[:50]}...")
            pdf_path = self.create_pdf(subtopic)
            generated_files.append(pdf_path)
        
        print()
        print(f"✅ Successfully created {len(generated_files)} PDFs")
        print(f"📂 Output location: {self.output_dir.absolute()}")
        
        return generated_files


def main():
    """Main entry point for CLI usage."""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python split_chapter.py <input_file.pdf|input_file.txt>")
        print()
        print("Example:")
        print("  python split_chapter.py chapter1.pdf")
        print("  python split_chapter.py chapter1.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Optional: custom output directory
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output_subtopics"
    
    try:
        # Create splitter and process
        splitter = ChapterSplitter(input_file, output_dir)
        generated_files = splitter.process()
        
        # Print summary
        print()
        print("=" * 60)
        print("GENERATED FILES:")
        print("=" * 60)
        for filepath in generated_files:
            print(f"  • {Path(filepath).name}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
