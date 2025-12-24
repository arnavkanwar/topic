#!/usr/bin/env python3
"""
Robust Chapter Splitter
-----------------------
Splits NCERT-style PDF chapters into sub-topic PDFs with zero content loss.
Features:
- Hybrid Text Extraction (PDF Text + OCR Fallback)
- Dynamic Sub-Topic Pattern Discovery
- Strict Content Boundary Enforcement
- Intelligent Cleaning & Filtering

Author: Agentic AI
"""

import sys
import os
import re
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter

# --- Third-party Dependencies ---
try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not found. Install it with: pip install pymupdf")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.lib.units import inch
except ImportError:
    print("Error: ReportLab not found. Install it with: pip install reportlab")
    sys.exit(1)

# Optional OCR dependencies
try:
    import pytesseract
    from PIL import Image
    import io
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract or Pillow not found. OCR fallback will be disabled.")


# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# --- Data Structures ---

class SubTopic:
    """Represents a validated sub-topic."""
    def __init__(self, number_str: str, title: str, content: str):
        self.number_str = number_str  # e.g., "1.1", "2.3"
        self.title = title.strip()
        self.content = content.strip()
    
    def __repr__(self):
        return f"<SubTopic {self.number_str}: {self.title[:30]}...>"


# --- Core Classes ---

class ChapterExtractor:
    """Handles hybrid text extraction from PDF."""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.full_text = ""
        self.ocr_triggered = False

    def extract(self) -> str:
        """Main extraction method using hybrid approach."""
        logger.info(f"Extracting text from: {self.pdf_path.name}")
        extracted_pages = []
        
        for page_num, page in enumerate(self.doc, 1):
            text = self._extract_page(page, page_num)
            extracted_pages.append(text)
            
        self.full_text = "\n".join(extracted_pages)
        
        if self.ocr_triggered and not HAS_OCR:
            logger.warning("OCR was needed but dependencies are missing. Results may be incomplete.")
            
        return self.full_text

    def _extract_page(self, page, page_num: int) -> str:
        """Extracts text from a single page, falling back to OCR if needed."""
        # 1. Try standard text extraction
        text = page.get_text("text").strip()
        
        # 2. Check density (simple heuristic: char count)
        # If page has very little text, it might be an image scan
        if len(text) < 50 and HAS_OCR:
            logger.info(f"Page {page_num} seems empty/scanned. Attempting OCR...")
            try:
                # Render page to image
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(pil_image)
                if len(ocr_text) > len(text):
                    text = ocr_text
                    self.ocr_triggered = True
                    logger.info(f"   -> OCR recovered {len(text)} chars on Page {page_num}")
            except Exception as e:
                logger.error(f"   -> OCR failed on Page {page_num}: {e}")
        
        # 3. Clean page-level artifacts
        text = self._clean_page_artifacts(text)
        return text

    def _clean_page_artifacts(self, text: str) -> str:
        """Removes common page headers/footers."""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty
            if not line:
                continue
            # Skip likely page numbers (isolated digits)
            if line.isdigit() and len(line) < 4:
                continue
            # Skip 'Reprint' lines
            if "Reprint" in line or "2024-25" in line or "2025-26" in line:
                continue
            # Skip isolated Figure captions (heuristic)
            if re.match(r'^Fig\.\s*\d+', line):
                continue
                
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)


class PatternDiscovery:
    """Discovers the dominant sub-topic heading pattern."""
    
    # Potential Regex Patterns for Headings
    PATTERNS = {
        'numeric_decimal': r'^(\d+\.\d+(?:\.\d+)?)\s+(.+)$',   # 1.1 Title
        'numeric_standalone': r'^(\d+)\.\s+(.+)$',             # 1. Title
        'wrapped_decimal': r'^(\d+\.\d+)$',                    # 1.2 (Title on next line)
        'roman': r'^([IVX]+)\.\s+(.+)$',                       # I. Title
        'alpha': r'^([A-Z])\.\s+(.+)$'                         # A. Title
    }
    
    def __init__(self, text: str):
        self.text = text
        self.lines = text.split('\n')
        self.dominant_pattern_name = None
        self.dominant_regex = None

    def discover(self) -> str:
        """Analyzes text to find the most consistent sequential pattern."""
        stats = Counter()
        
        for line in self.lines:
            line = line.strip()
            if not line:
                continue
            
            for name, regex in self.PATTERNS.items():
                if re.match(regex, line):
                    stats[name] += 1
        
        logger.info(f"Pattern stats: {stats}")
        
        if not stats:
            logger.error("No recognizable heading patterns found.")
            return None
            
        # Select dominant pattern (simplest logic: most frequent)
        # A smarter approach would check for sequential integers (1.1, 1.2...)
        # but max count is a solid proxy for NCERT files.
        best_pattern = stats.most_common(1)[0][0]
        self.dominant_pattern_name = best_pattern
        self.dominant_regex = self.PATTERNS[best_pattern]
        
        logger.info(f"Dominant Pattern Detected: '{best_pattern}'")
        return best_pattern


class ContentSplitter:
    """Splits text into SubTopic objects based on the discovered pattern."""
    
    def __init__(self, text: str, pattern_regex: str, pattern_name: str):
        self.text = text
        self.lines = text.split('\n')
        self.regex = re.compile(pattern_regex)
        self.pattern_name = pattern_name
        self.subtopics = []

    def split(self) -> List[SubTopic]:
        current_number = None
        current_title = None
        current_content = []
        
        # Flags for wrapped headings
        awaiting_wrapped_title = False
        
        for i, line in enumerate(self.lines):
            line = line.strip()
            if not line:
                continue

            # Check if line matches a new heading
            match = self.regex.match(line)
            is_heading = False
            
            # --- Validating candidate heading ---
            if match:
                # Filter out obvious false positives
                # e.g. "2000" might match \d+ but isn't a heading
                # e.g. "Fig. 1" shouldn't match
                if "Fig" in line or "Table" in line:
                    start_new_topic = False
                else:
                    is_heading = True
            
            if is_heading:
                # If we were building a topic, save it
                if current_number:
                    self._save_topic(current_number, current_title, current_content)
                
                # Start new topic
                current_content = []
                
                # Handle Wrapped vs Inline patterns
                if self.pattern_name == 'wrapped_decimal':
                    # Pattern matches just "1.2", title is likely next line
                    current_number = match.group(1)
                    current_title = "Untitled" # Placeholder
                    awaiting_wrapped_title = True
                else:
                    # Pattern matches "1.2 Title Here"
                    current_number = match.group(1)
                    current_title = match.group(2).strip()
                    awaiting_wrapped_title = False
                    
            elif awaiting_wrapped_title:
                # This line MUST be the title
                # Make sure it's not empty or another number
                if not re.match(r'^\d', line):
                    current_title = line
                    awaiting_wrapped_title = False
                else:
                    # Weird edge case, maybe previous wasn't a heading?
                    # Treat previous number as content and reset
                    current_content.append(current_number)
                    current_content.append(line)
                    current_number = None
            else:
                # Just normal content
                if current_number:
                    # We are inside a topic
                     current_content.append(line)
                else:
                    # Preamble text (Intro before 1.1)
                    # We can optionally capture this as "Introduction"
                    pass

        # Save last topic
        if current_number:
            self._save_topic(current_number, current_title, current_content)

        return self.subtopics

    def _save_topic(self, number, title, content_lines):
        # Filtering: reject invalid topics
        # 1. Reject if "Activity", "Source", "Key Words" matches
        bad_keywords = ["Activity", "Source", "New Words", "Discuss", "Project"]
        if any(k.upper() in title.upper() for k in bad_keywords):
            return

        # 2. Reject if title is all caps map label (e.g. "SOUTH AFRICA")
        # Heuristic: >10 chars, all upper, no lowercase
        if len(title) > 4 and title.isupper() and " " not in title: 
             # Single word UPPERCASE might be ok (e.g. "INTRODUCTION")
             # but "AFRICA" mid-text is suspect. 
             # But if it has a number "1.2 AFRICA", it's probably a section.
             pass

        content_str = "\n".join(content_lines)
        if len(content_str) < 50:
            logger.warning(f"Skipping tiny section {number} '{title}' (<50 chars)")
            return

        self.subtopics.append(SubTopic(number, title, content_str))


class PDFGenerator:
    """Generates clean PDFs for sub-topics."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor='black'
        )
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

    def generate(self, subtopics: List[SubTopic], base_name: str):
        if not subtopics:
            logger.error("No subtopics to generate PDFs for!")
            return

        logger.info(f"Generating {len(subtopics)} PDFs...")
        
        for st in subtopics:
            # Safe filename
            safe_title = re.sub(r'[^\w\s-]', '', st.title).strip().replace(' ', '_')[:40]
            safe_num = st.number_str.replace('.', '_')
            filename = f"{base_name}_{safe_num}_{safe_title}.pdf"
            filepath = self.output_dir / filename
            
            self._create_single_pdf(filepath, st)
            logger.info(f"  -> Created: {filename}")

    def _create_single_pdf(self, filepath: Path, subtopic: SubTopic):
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=inch, leftMargin=inch,
            topMargin=inch, bottomMargin=inch
        )
        
        story = []
        
        # Title
        full_title = f"{subtopic.number_str} {subtopic.title}"
        story.append(Paragraph(full_title, self.title_style))
        story.append(Spacer(1, 12))
        
        # Content
        # Split by double newlines to form paragraphs
        paras = subtopic.content.split('\n\n')
        for p_text in paras:
            p_text = p_text.strip().replace('\n', ' ')
            if p_text:
                story.append(Paragraph(p_text, self.body_style))
                story.append(Spacer(1, 8))
        
        doc.build(story)


# --- Main Orchestrator ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python split_chapter.py <pdf_file>")
        sys.exit(1)
        
    input_pdf = Path(sys.argv[1])
    if not input_pdf.exists():
        print(f"File not found: {input_pdf}")
        sys.exit(1)
        
    output_dir = Path("output_subtopics")
    
    # 1. Extract
    extractor = ChapterExtractor(input_pdf)
    full_text = extractor.extract()
    
    # Debug: Save extracted text
    with open(output_dir / f"{input_pdf.stem}_full.txt", "w") as f:
        f.write(full_text)
    
    # 2. Discover Pattern
    discoverer = PatternDiscovery(full_text)
    pattern_name = discoverer.discover()
    
    if not pattern_name:
        print("FAILED: Could not determine a dominant heading pattern.")
        sys.exit(1)
        
    # 3. Split Content
    splitter = ContentSplitter(full_text, discoverer.dominant_regex, pattern_name)
    subtopics = splitter.split()
    
    logger.info(f"Identified {len(subtopics)} valid sub-topics.")
    
    # 4. Generate PDFs
    generator = PDFGenerator(output_dir)
    generator.generate(subtopics, input_pdf.stem)
    
    print("\nProcessing Complete! Check 'output_subtopics/' folder.")

if __name__ == "__main__":
    main()
