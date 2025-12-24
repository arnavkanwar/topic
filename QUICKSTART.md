# Quick Start Guide

## Installation (One-Time Setup)

### Option 1: Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install pdfplumber PyMuPDF reportlab
```

### Option 2: System-wide Installation
```bash
pip install pdfplumber PyMuPDF reportlab
```

---

## Usage

### Run the program:
```bash
# With virtual environment
source venv/bin/activate
python split_chapter.py your_chapter.pdf

# OR without virtual environment
python3 split_chapter.py your_chapter.txt
```

### Output:
All PDFs will be saved in `output_subtopics/` folder

---

## Test with Sample File

```bash
source venv/bin/activate
python split_chapter.py sample_chapter.txt
```

This will create 5 PDFs in the `output_subtopics/` folder.

---

## File Structure

```
topic/
├── split_chapter.py          # Main program
├── README.md                 # Full documentation
├── QUICKSTART.md            # This file
├── sample_chapter.txt       # Test file
├── venv/                    # Virtual environment (after setup)
└── output_subtopics/        # Generated PDFs (after running)
    ├── sample_chapter_01_....pdf
    ├── sample_chapter_02_....pdf
    └── ...
```

---

## Common Issues

**"No module named 'pdfplumber'"**
→ Run: `pip install pdfplumber PyMuPDF reportlab`

**"No sub-topics detected"**
→ Your document needs clear headings (numbered or Title Case)

**"command not found: pip"**
→ Use `pip3` instead of `pip`

---

## Next Steps

1. ✅ Test with `sample_chapter.txt`
2. ✅ Try with your own PDF or TXT files
3. ✅ Check the `output_subtopics/` folder for results
4. ✅ Read `README.md` for detailed documentation
