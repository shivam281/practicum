# resume_utils.py

import pdfplumber
import docx

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return '\n'.join(page.extract_text() or '' for page in pdf.pages)

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return '\n'.join(para.text for para in doc.paragraphs)
