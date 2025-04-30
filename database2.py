import pandas as pd
import mysql.connector
from sentence_transformers import SentenceTransformer, util
import re
import spacy
import os

# Load models just once
model = SentenceTransformer('distilbert-base-nli-mean-tokens')
nlp = spacy.load("en_core_web_sm")

# Helper functions (reuse from your code)
def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[\r|\n|\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def resume_grade_with_suggestions(resume_text):
    suggestions = []
    if "project" not in resume_text.lower():
        suggestions.append("Your resume lacks project details. Consider adding details about projects you've worked on.")
    if len(re.findall(r"experience", resume_text, re.IGNORECASE)) == 0:
        suggestions.append("Consider adding your work experience section.")
    return suggestions

def get_semantic_score(resume_text, job_desc):
    emb_resume = model.encode(resume_text, convert_to_tensor=True)
    emb_job = model.encode(job_desc, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(emb_resume, emb_job)
    return float(similarity[0][0]) * 100

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

# Load your CSV
df = pd.read_excel("C:\\Users\\SANIA\\OneDrive\\Desktop\\resume\\Advanced_Cleaned_Resume.csv")

# Dummy Job Description for semantic scoring (you can customize this)
sample_job_desc = "Looking for a Python developer with experience in machine learning and SQL."

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="resume_db"
)
cursor = conn.cursor()

# Create new table with enhancements
cursor.execute("""
CREATE TABLE IF NOT EXISTS enhanced_resume_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    CandidateName VARCHAR(255),
    Resume_str LONGTEXT,
    Category VARCHAR(255),
    Cleaned_Resume LONGTEXT,
    Entities TEXT,
    SemanticScore FLOAT,
    Suggestions TEXT
)
""")

# Insert enhanced data
for _, row in df.iterrows():
    raw_resume = row["Resume_str"]
    cleaned = clean_text(raw_resume)
    suggestions = resume_grade_with_suggestions(cleaned)
    semantic_score = get_semantic_score(cleaned, sample_job_desc)
    entities = extract_entities(raw_resume)
    candidate_name = entities["names"][0] if entities["names"] else "Unknown"

    cursor.execute("""
        INSERT INTO enhanced_resume_data (
            CandidateName, Resume_str, Category, Cleaned_Resume,
            Entities, SemanticScore, Suggestions
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        candidate_name,
        raw_resume,
        row["Category"],
        cleaned,
        str(entities),
        semantic_score,
        ", ".join(suggestions)
    ))

conn.commit()
cursor.close()
conn.close()
print("✅ Enhanced resumes loaded with grading, suggestions, and scoring.")
