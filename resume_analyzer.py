# resume_processor.py
import os
import re
import docx2txt
from resumatic.resume_utils import extract_text_from_pdf, extract_text_from_docx
import pandas as pd
from PyPDF2 import PdfReader
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import spacy


nlp = spacy.load("en_core_web_sm")

# Keywords to search
SKILL_KEYWORDS = ["python", "java", "sql", "machine learning", "deep learning", "nlp", "data analysis", "html", "css", "javascript"]

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print("❌ PDF extraction error:", e)
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    try:
        return docx2txt.process(file_path)
    except Exception as e:
        print("❌ DOCX extraction error:", e)
        return ""

# Universal parser for PDF/DOCX

def parse_resume(file_path):
    if file_path.endswith(".pdf"):
        return clean_text(extract_text_from_pdf(file_path))
    elif file_path.endswith(".docx"):
        return clean_text(extract_text_from_docx(file_path))
    else:
        print("❌ Unsupported file format:", file_path)
        return ""

# Text cleaner & entity extractor
def clean_text(text):
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    filtered = [w for w in tokens if not w in stop_words]
    return " ".join(filtered)

# Skill extractor
def extract_skills(text):
    return [skill for skill in SKILL_KEYWORDS if skill in text]

# Entity extractor (Name, Email, Phone etc.)
def extract_entities(text):
    doc = nlp(text)
    entities = {"names": [], "emails": [], "phones": []}
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["names"].append(ent.text)
    emails = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    phones = re.findall(r"\+?\d[\d -]{8,}\d", text)
    entities["emails"] = emails
    entities["phones"] = phones
    return entities

# Dummy recommender based on missing skills
def recommend_certifications(skills):
    recommended = []
    if "machine learning" not in skills:
        recommended.append("Machine Learning by Andrew Ng - Coursera")
    if "sql" not in skills:
        recommended.append("SQL for Data Science - Coursera")
    return recommended

# Export database table to CSV
def export_to_csv(connection, table_name, output_file):
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, connection)
        df.to_csv(output_file, index=False)
        print(f"✅ Exported {table_name} to {output_file}")
    except Exception as e:
        print("❌ Error exporting table:", e)

# Example usage
if __name__ == "__main__":
    filepath = "./sample_resume.pdf"
    resume_text = parse_resume(filepath)
    cleaned_resume = clean_text(resume_text)
    skills = extract_skills(cleaned_resume)
    entities = extract_entities(resume_text)
    certifications = recommend_certifications(skills)

    print("Cleaned Resume:\n", cleaned_resume[:300])
    print("Skills:", skills)
    print("Entities:", entities)
    print("Certifications:", certifications)
