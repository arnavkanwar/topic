# Chapter Splitter - Installation & Usage Guide

## 📦 Installation

### Step 1: Install Required Libraries

Run the following command to install all dependencies:

```bash
pip install pdfplumber PyMuPDF reportlab
```

**Library Breakdown:**
- **pdfplumber**: Primary PDF text extraction (recommended)
- **PyMuPDF (fitz)**: Fallback PDF extraction library
- **reportlab**: PDF generation with formatting

### Step 2: Verify Installation

```bash
python split_chapter.py --help
```

---

## 🚀 Usage

### Basic Usage

```bash
python split_chapter.py input_chapter.pdf
```

```bash
python split_chapter.py input_chapter.txt
```

### Custom Output Directory

```bash
python split_chapter.py input_chapter.pdf my_custom_output/
```

---

## 🧠 How Sub-Topic Detection Works

The program uses **regex pattern matching** to identify headings in the document. It looks for:

### 1. **Numbered Headings**
```
1. Introduction to History
2. The Ancient Civilizations
3. Medieval Period
```
Pattern: `^\d+\.\s+[A-Z]...`

### 2. **Roman Numeral Headings**
```
I. Introduction
II. Main Content
III. Conclusion
```
Pattern: `^[IVX]+\.\s+[A-Z]...`

### 3. **Alphabetic Headings**
```
A. First Topic
B. Second Topic
C. Third Topic
```
Pattern: `^[A-Z]\.\s+[A-Z]...`

### 4. **All Caps Titles**
```
INTRODUCTION TO THE TOPIC
MAIN DISCUSSION POINTS
```
Pattern: `^[A-Z][A-Z\s]{10,80}$`

### 5. **Title Case Headings**
```
Introduction To Modern History
The Rise Of Empires
Cultural Development
```
Pattern: `^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$`

### Detection Algorithm:

1. **First Pass**: Scan all lines and match against heading patterns
2. **Second Pass**: Extract content between consecutive headings
3. **Content Assignment**: Everything from one heading to the next becomes that sub-topic's content
4. **PDF Generation**: Each sub-topic gets its own formatted PDF

---

## 📂 Example Output Structure

After running the program on `NCERT_History_Chapter1.pdf`:

```
output_subtopics/
├── NCERT_History_Chapter1_01_Introduction_to_History.pdf
├── NCERT_History_Chapter1_02_The_Ancient_Civilizations.pdf
├── NCERT_History_Chapter1_03_Medieval_Period.pdf
├── NCERT_History_Chapter1_04_Modern_Era.pdf
└── NCERT_History_Chapter1_05_Conclusion.pdf
```

**Filename Format:**
```
<Chapter_Name>_<Number>_<Subtopic_Title>.pdf
```

---

## 🎨 PDF Output Features

Each generated PDF includes:

- ✅ **Professional formatting** with proper margins (0.75 inch)
- ✅ **Bold heading** at the top (16pt Helvetica Bold)
- ✅ **Justified body text** (11pt Helvetica)
- ✅ **Proper paragraph spacing**
- ✅ **Clean, readable layout**

---

## ⚠️ Error Handling

The program handles:

| Error | Behavior |
|-------|----------|
| File not found | Clear error message with file path |
| Unsupported format | Only .pdf and .txt allowed |
| No sub-topics detected | Suggests checking file formatting |
| Empty/corrupted file | Validates minimum content length |
| PDF extraction failure | Tries pdfplumber → PyMuPDF fallback |

---

## 🔧 Troubleshooting

### No sub-topics detected?

**Solution:** Your document may not have clear heading patterns. Try:
- Adding numbered headings (1., 2., 3.)
- Using Title Case for section headings
- Using ALL CAPS for major sections

### Poor text extraction from PDF?

**Solution:** 
- Try converting PDF to text first: `pdftotext input.pdf output.txt`
- Use the .txt file as input instead

### Installation issues?

**Solution:**
```bash
# Use pip with --upgrade flag
pip install --upgrade pdfplumber PyMuPDF reportlab

# Or use pip3 on some systems
pip3 install pdfplumber PyMuPDF reportlab
```

---

## 📝 Example Test Run

```bash
$ python split_chapter.py sample_chapter.pdf

📖 Processing: sample_chapter.pdf
📁 Output directory: output_subtopics

🔍 Extracting text...
   ✓ Extracted 15420 characters
🧹 Cleaning text...
   ✓ Cleaned to 15180 characters
🎯 Detecting sub-topics...
   ✓ Found 5 sub-topics

📄 Generating PDFs...
   [1/5] Introduction to History...
   [2/5] The Ancient Civilizations...
   [3/5] Medieval Period...
   [4/5] Modern Era...
   [5/5] Conclusion...

✅ Successfully created 5 PDFs
📂 Output location: /path/to/output_subtopics

============================================================
GENERATED FILES:
============================================================
  • sample_chapter_01_Introduction_to_History.pdf
  • sample_chapter_02_The_Ancient_Civilizations.pdf
  • sample_chapter_03_Medieval_Period.pdf
  • sample_chapter_04_Modern_Era.pdf
  • sample_chapter_05_Conclusion.pdf
============================================================
```

---

## 🎯 Code Structure

The program is organized into:

- **`SubTopic` class**: Data structure for storing sub-topic info
- **`ChapterSplitter` class**: Main processing logic
  - `extract_text()`: PDF/TXT text extraction
  - `clean_text()`: Whitespace normalization
  - `detect_subtopics()`: Heading pattern matching
  - `create_pdf()`: PDF generation with reportlab
  - `process()`: Orchestrates the entire workflow
- **`main()` function**: CLI entry point

---

## 📄 License

MIT License - Free to use and modify

---

## 🤝 Contributing

Feel free to enhance the heading detection patterns or add new features!
