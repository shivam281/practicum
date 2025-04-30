# utils/db_loader.py
def load_csv_to_enhanced_db(file_path):
    import pandas as pd
    import mysql.connector
    from sentence_transformers import SentenceTransformer, util
    import spacy
    import re

    model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    nlp = spacy.load("en_core_web_sm")

    def clean_text(text):
        return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()

    def resume_grade_with_suggestions(resume_text):
        suggestions = []
        grade = 0
        if len(resume_text.split()) > 300:
            grade += 1
        else:
            suggestions.append("Your resume is quite short. Consider expanding with more details.")

        if "project" not in resume_text.lower():
            suggestions.append("Add project details to showcase your hands-on experience.")
        else:
            grade += 1

        return grade, " | ".join(suggestions)

    def get_semantic_score(resume_text, job_desc):
        embeddings = model.encode([resume_text, job_desc])
        return float(util.pytorch_cos_sim(embeddings[0], embeddings[1])[0][0])

    def extract_entities(text):
        doc = nlp(text)
        skills = list(set([ent.text for ent in doc if ent.pos_ == "NOUN"]))
        return skills

    df = pd.read_csv(file_path)
    job_desc = "Looking for a Python developer with experience in machine learning and SQL."

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="resumedb"
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enhanced_resume_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            resume_text LONGTEXT,
            cleaned_text LONGTEXT,
            skills TEXT,
            grade INT,
            suggestions TEXT,
            semantic_score FLOAT
        )
    """)

    for _, row in df.iterrows():
        name = row['Name']
        email = row['Email']
        resume_text = row['Resume']
        cleaned = clean_text(resume_text)
        skills = ", ".join(extract_entities(cleaned))
        grade, suggestions = resume_grade_with_suggestions(cleaned)
        semantic_score = get_semantic_score(cleaned, job_desc)

        cursor.execute("""
            INSERT INTO enhanced_resume_data (name, email, resume_text, cleaned_text, skills, grade, suggestions, semantic_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, resume_text, cleaned, skills, grade, suggestions, semantic_score))

    conn.commit()
    cursor.close()
    conn.close()
