import streamlit as st
import pymysql
import pandas as pd
from pypdf import PdfReader
import re
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
import plotly.express as px
import spacy
from fpdf import FPDF
from collections import Counter
from textblob import TextBlob
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# ----------------------------------------------------------- STYLING -------------------------------------------------------------------
def apply_custom_styles():
    custom_style = """
        <style>
            .stApp { background-color: #F0F8FF; }
            section[data-testid="stSidebar"] { background-color: #2E3B55 !important; }
            section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
            h1, h2, h3, h4, h5, h6, p, div, span, button { color: #2E3B55 !important; }
        </style>
    """
    st.markdown(custom_style, unsafe_allow_html=True)

apply_custom_styles()

# ----------------------------------------------------------- UTILITY FUNCTIONS -------------------------------------------------------------------
def export_to_pdf(text, filename="analysis_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
    pdf.output(filename)

def download_csv(df, filename="resume_analysis.csv"):
    return df.to_csv(index=False).encode("utf-8")

def fetch_resume_data():
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME")
        )
        cursor = connection.cursor()
        cursor.execute("SELECT Resume_str, Category, Cleaned_Resume, Entities FROM resume_data;")
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=["Resume_str", "Category", "Cleaned_Resume", "Entities"])
        cursor.close()
        connection.close()
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

def pdf_to_text(pdf_file):
    if pdf_file:
        reader = PdfReader(pdf_file)
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    return ""

def clean_text(text):
    if text:
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = re.sub(r'[\r|\n|\r\n]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
    return text

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

semantic_model = load_model()
nlp = spacy.load("en_core_web_sm")

# Add skill patterns to spaCy
skills_list = ["Python", "Machine Learning", "SQL", "Web Development", "Data Structures"]
ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.add_patterns([{"label": "SKILL", "pattern": skill} for skill in skills_list])

def extract_entities(resume_text):
    doc = nlp(resume_text)
    return [(ent.text, ent.label_) for ent in doc.ents]

def show_resume_pie(skills, resume_text, recommended):
    exp_mentions = len(re.findall(r"(\d+\+?\s*years?)", resume_text.lower()))
    values = [len(skills), exp_mentions, len(recommended)]
    labels = ["Skills", "Experience Mentions", "Certifications Needed"]
    
    fig = px.pie(values=values, names=labels, title="Resume Content Distribution",
                 color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(fig)

# ----------------------------------------------------------- PAGE NAVIGATION -------------------------------------------------------------------
page = st.sidebar.radio("📍 Select Page", ["Home", "Analyze Resume", "AI Interview", "Leaderboard", "Database Records", "Recruiter Dashboard"])

# ----------------------------------------------------------- HOME PAGE -------------------------------------------------------------------
if page == "Home":
    st.markdown("<h1>📃 Resume Analyzer & AI Interview</h1>", unsafe_allow_html=True)
    st.markdown("<h3>🚀 Analyze Resumes | 🗣️ Conduct AI Interviews | 🏆 Track Performance</h3>", unsafe_allow_html=True)
    img_path = "img.jpg"
    if os.path.exists(img_path):
        st.image (img_path, use_container_width=True)
    else:
        st.warning("⚠️ Image file not found! Please add 'img.jpg' to the project directory.")

# ----------------------------------------------------------- ANALYZ E RESUME PAGE -------------------------------------------------------------------
elif page == "Analyze Resume":
    st.header("📁 Analyze Resume")
    
    candidate_name = st.text_input("Enter Candidate Name", value=st.session_state.get("candidate_name", ""))
    if candidate_name:
        st.session_state.candidate_name = candidate_name

    job_description = st.text_area("Enter the job description:")
    pdf_file = st.file_uploader("Upload PDF resume:", type=['pdf'])

    certifications = {
        "Python": "Udemy - Complete Python Bootcamp",
        "Machine Learning": "Coursera - Machine Learning by Andrew Ng",
        "SQL": "DataCamp - SQL Fundamentals",
        "Web Development": "freeCodeCamp - Web Design",
        "Data Structures": "GeeksforGeeks - DSA Self-Paced"
    }

    def recommend_certifications(job_desc, resume):
        return [cert for skill, cert in certifications.items() if skill.lower() in job_desc.lower() and skill.lower() not in resume.lower()]

    def get_semantic_score(resume_text, job_desc):
        emb_resume = semantic_model.encode(resume_text, convert_to_tensor=True)
        emb_job = semantic_model.encode(job_desc, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(emb_resume, emb_job)
        return float(similarity[0][0]) * 100

    def extract_skills(resume_text):
        doc = nlp(resume_text)
        skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]
        return skills

    if pdf_file:
        resume_text = clean_text(pdf_to_text(pdf_file))
        st.session_state.resume_text = resume_text

        if job_description:
            semantic_score = get_semantic_score(resume_text, job_description)
            st.success(f"🧐 Semantic Match Score: **{semantic_score:.2f}%**")

            recommended = recommend_certifications(job_description, resume_text)
            if recommended:
                st.markdown("🌟 **Recommended Certifications to improve your resume:**")
                for rec in recommended:
                    st.markdown(f"- {rec}")

            # Skill extraction and visualization
            skills = extract_skills(resume_text)
            show_resume_pie(skills, resume_text, recommended)
            skill_counts = Counter(skills)
            skill_df = pd.DataFrame(skill_counts.items(), columns=['Skill', 'Count'])
            st.bar_chart(skill_df.set_index('Skill'))

            if st.button("📄 Export Summary as PDF"):
                pdf_summary = f"""
                Semantic Match Score: {semantic_score:.2f}%
                Recommended Certifications: {', '.join(recommended) if recommended else 'None'}
                Extracted Skills: {', '.join(skills) if skills else 'None'}
                """
                export_to_pdf(pdf_summary)
                st.success("PDF exported as analysis_report.pdf")

            if st.button("📅 Download Analysis as CSV"):
                export_data = pd.DataFrame({"Semantic Score": [semantic_score], "Recommended Certifications": [", ".join(recommended)], "Extracted Skills": [", ".join(skills)]})
                csv_data = download_csv(export_data)
                st.download_button("Download CSV", data=csv_data, file_name="resume_analysis.csv", mime="text/csv")

            if st.button("📄 Export Feedback as PDF"):
                feedback = "Here is the feedback for the resume analysis..."  # Customize feedback based on analysis
                export_to_pdf(feedback, filename="resume_feedback.pdf")
                st.success("Feedback exported as resume_feedback.pdf")

        if st.button("Extract Resume Info"):
            st.write("Named Entities:", extract_entities(resume_text))

        if job_description and resume_text:
            missing_skills = [skill for skill in certifications.keys() if skill.lower() not in resume_text.lower()]
            if missing_skills:
                st.markdown("❌ **Missing Skills:**")
                for skill in missing_skills:
                    st.markdown(f"- {skill}")

# ----------------------------------------------------------- AI INTERVIEW PAGE -----------------------------------------------------------
elif page == "AI Interview":
    st.header("🗣️ AI Interview Chatbot")

    if "leaderboard" not in st.session_state:
        st.session_state.leaderboard = []

    candidate_name = st.text_input("Enter Candidate Name", value=st.session_state.get("candidate_name", ""))
    if candidate_name:
        st.session_state.candidate_name = candidate_name

    resume_text = st.session_state.get("resume_text", "")

    if resume_text:
        st.write("Resume text loaded for interview.")

    def generate_questions(resume_text):
        skills = ["Python", "Machine Learning", "SQL", "Data Structures", "Web Development"]
        projects = re.findall(r"project[\s\S]{0,100}", resume_text, re.IGNORECASE)
        questions = [f"Can you explain your experience with {skill}?" for skill in skills if skill.lower() in resume_text .lower()]
        questions += [f"Tell me about this project: '{proj.strip()}'. What were the challenges?" for proj in projects]
        return questions if questions else ["Describe a technical problem you solved recently."]

    reference_answers = {
        "Python": "I have used Python extensively for scripting, data analysis, and automation tasks.",
        "SQL": "I am proficient in SQL and have used it for querying databases, joins, and data cleaning.",
        "Web Development": "I’ve built web apps using HTML, CSS, JavaScript, and React.",
        "Machine Learning": "I’ve worked on ML projects using scikit-learn and TensorFlow.",
        "Data Structures": "I’ve practiced DSA through coding platforms and solved problems involving arrays, trees, and graphs."
    }

    def explain_similarity(user_answer, question_text):
        matched_keywords = []
        for skill in reference_answers:
            if skill.lower() in question_text.lower() and skill.lower() in user_answer.lower():
                matched_keywords.append(skill)

        if matched_keywords:
            st.caption(f"✅ Matched keywords: {', '.join(matched_keywords)}")
        else:
            st.caption("⚠️ No direct skill keywords matched. Try including more technical terms.")

        generic_answer = "I have experience in various technical areas and can adapt to new challenges."
        user_embed = semantic_model.encode(user_answer, convert_to_tensor=True)
        ref_embed = semantic_model.encode(generic_answer, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(user_embed, ref_embed)
        return round(float(similarity[0][0]) * 10, 2)

    def generate_personalized_feedback(answer):
        blob = TextBlob(answer)
        sentiment = blob.sentiment.polarity
        feedback = "Your answer was "
        if sentiment > 0.3:
            feedback += "positive and confident."
        elif sentiment < -0.1:
            feedback += "a bit negative. Try to focus on achievements."
        else:
            feedback += "neutral. Try to elaborate more."

        if len(blob.sentences) < 2:
            feedback += " Consider expanding your answers with more details."
        return feedback

    if candidate_name and resume_text:
        questions = generate_questions(resume_text)

        total_score = 0
        st.write("### 🤖 Interview Questions")

        temp_answers = {}

        for idx, question in enumerate(questions):
            with st.form(f"form_{idx}"):
                st.write("💬", question)
                key_ans = f"answer_{idx}"
                answer = st.text_area(f"Your Answer ({question[:20]}...)", key=key_ans, value=st.session_state.get(key_ans, ""))

                submitted = st.form_submit_button(f"Submit Answer ({question[:20]}...)")
                if submitted:
                    score = explain_similarity(answer, question)
                    temp_answers[key_ans] = answer
                    total_score += score
                    st.success(f"Score for this answer: {score}/10")
                    st.info(generate_personalized_feedback(answer))

        if st.button("📊 Submit Interview"):
            for key in temp_answers:
                st.session_state[key] = temp_answers[key]
            st.success(f"Final Score: {total_score}/{10 * len(questions)}")
            st.session_state.leaderboard.append({"Name": candidate_name, "Score": total_score})

            # Save interview history to the database
            try:
                connection = pymysql.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    db=os.getenv("DB_NAME")
                )
                cursor = connection.cursor()
                cursor.execute("INSERT INTO interview_history (candidate_name, score, responses) VALUES (%s, %s, %s)",
                               (candidate_name, total_score, str(temp_answers)))
                connection.commit()
                cursor.close()
                connection.close()
            except Exception as e:
                st.error(f"❌ Error saving interview history: {e}")

            # Fetch leaderboard from the database
            try:
                connection = pymysql.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    db=os.getenv("DB_NAME")
                )
                cursor = connection.cursor()
                cursor.execute("SELECT candidate_name, score FROM interview_history ORDER BY score DESC;")
                leaderboard_data = cursor.fetchall()
                st.subheader("🏆 Leaderboard")
                st.write(pd.DataFrame(leaderboard_data, columns=["Name", "Score"]))
                cursor.close()
                connection.close()
            except Exception as e:
                st.error(f"❌ Error fetching leaderboard: {e}")

            # Define reference_answers with a list of important skills/keywords that should be in the resume
            reference_answers = ["Python", "Machine Learning", "Data Structures", "SQL", "Deep Learning", "Web Development"]

# Generate feedback by checking for weaknesses (skills not found in resume)
            feedback = "Strengths: "  # Example placeholder for strengths
            feedback += "Weaknesses: " + ", ".join([skill for skill in reference_answers if skill.lower() not in resume_text.lower()]) + "."

# Display feedback in Streamlit
            st.markdown("### Feedback:")
            st.write(feedback)


            if st.button("📄 Export Feedback as PDF"):
                export_to_pdf(feedback, filename="interview_feedback.pdf")
                st.success("Feedback exported as interview_feedback.pdf")

    else:
        st.warning("⚠️ Upload a resume & enter name before starting.")

# ----------------------------------------------------------- RECRUITER DASHBOARD -------------------------------------------------------------------
elif page == "Recruiter Dashboard":
    st.header("📊 Recruiter Dashboard")
    df = fetch_resume_data()
    if not df.empty:
        st.dataframe(df)
        category = st.selectbox("Filter by Category", df["Category"].unique())
        filtered_df = df[df["Category"] == category]
        st.subheader("Filtered Records")
        st.dataframe(filtered_df)
        if st.button("📅 Download Filtered Candidates (CSV)"):
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name=f"filtered_candidates_{category}.csv", mime="text/csv")

# ----------------------------------------------------------- DATABASE RECORDS PAGE -------------------------------------------------------------------
elif page == "Database Records":
    st.header("📊 Database Records")
    df = fetch_resume_data()
    if not df.empty:
        st.dataframe(df)
        if st.button("📅 Download All Records (CSV)"):
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="all_records.csv", mime="text/csv")
    else:
        st.info("No records available in the database.")

# ----------------------------------------------------------- LEADERBOARD -------------------------------------------------------------------
elif page == "Leaderboard":
    st.header("🏆 Leaderboard")
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME")
        )
        cursor = connection.cursor()
        cursor.execute("SELECT candidate_name, score FROM interview_history ORDER BY score DESC;")
        data = cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=["Candidate", "Score"])
            st.dataframe(df)
        else:
            st.info("No data found.")
        cursor.close()
        connection.close()
    except Exception as e:
        st.error(f"❌ Error fetching leaderboard: {e}")