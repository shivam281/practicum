import streamlit as st
import pymysql
import pandas as pd
from pypdf import PdfReader
import re
import random
import os

# ----------------------------------------------------------- UI SETTINGS -------------------------------------------------------------------
def apply_custom_styles():
    custom_style = """
        <style>
            .stApp {
                background-color: #F0F8FF;
            }
            section[data-testid="stSidebar"] {
                background-color: #2E3B55 !important;
            }
            section[data-testid="stSidebar"] * {
                color: #FFFFFF !important;
            }
            h1, h2, h3, h4, h5, h6, p, div, span, button {
                color: #2E3B55 !important;
            }
        </style>
    """
    st.markdown(custom_style, unsafe_allow_html=True)

apply_custom_styles()

# ----------------------------------------------------------- HOME PAGE -------------------------------------------------------------------
st.markdown("<h1>📃 Resume Analyzer & AI Interview</h1>", unsafe_allow_html=True)
st.markdown("<h3>🚀 Analyze Resumes | 🗣️ Conduct AI Interviews | 🏆 Track Performance</h3>", unsafe_allow_html=True)

# **Check if image exists before displaying**
img_path = "img.png"
if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.image("default_placeholder.png", use_container_width=True)  # Fallback image

# ----------------------------------------------------------- NAVIGATION BAR -------------------------------------------------------------------
page = st.sidebar.radio("📍 Select Page", ["Home", "Analyze Resume", "AI Interview", "Leaderboard", "Database Records"])

# ----------------------------------------------------------- DATABASE CONNECTION -------------------------------------------------------------------
def fetch_resume_data():
    """Fetch resume data from MySQL database"""
    try:
        connection = pymysql.connect(host='localhost', user='root', password='SAnia@2004', db='resume_db')
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

# ----------------------------------------------------------- PDF PROCESSING -------------------------------------------------------------------
def pdf_to_text(pdf_file):
    """Extract text from a PDF file."""
    if pdf_file is not None:
        reader = PdfReader(pdf_file)
        text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    return ""

def clean_text(text):
    """Clean extracted text from PDF."""
    if text:
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  
        text = re.sub(r'[\r|\n|\r\n]+', ' ', text)  
        text = re.sub(r'\s+', ' ', text).strip()  
    return text

# ----------------------------------------------------------- RESUME ANALYZER UI -------------------------------------------------------------------
if page == "Analyze Resume":
    st.header("📃 Resume Analyzer")

    st.subheader("Upload and Analyze Your Resume")
    job_description = st.text_area("Enter the job description:")
    pdf_file = st.file_uploader("Upload PDF resume:", type=['pdf'])

    if pdf_file:
        resume_text = pdf_to_text(pdf_file)
        resume_text = clean_text(resume_text)

        if job_description:
            st.subheader("📊 Mock ATS Analysis Result")
            ats_score = random.randint(50, 95)
            st.write(f"✅ **Your ATS Score:** **{ats_score}/100**")
            st.write("📌 **Suggestions:** Improve formatting, add keywords from job description.")
    else:
        st.warning("⚠️ Please upload a resume.")

# ----------------------------------------------------------- AI INTERVIEW CHATBOT -------------------------------------------------------------------
if page == "AI Interview":
    st.header("🗣️ AI Interview Chatbot")

    candidate_name = st.text_input("Enter Candidate Name")

    if "leaderboard" not in st.session_state:
        st.session_state.leaderboard = []

    def generate_questions(resume_text):
        """Generate interview questions based on keywords found in the resume."""
        keywords = ["Python", "Machine Learning", "SQL", "Data Structures", "Web Development"]
        matched_skills = [word for word in keywords if word.lower() in resume_text.lower()]
        questions = [f"Explain your experience with {skill}." for skill in matched_skills]
        return questions if questions else ["Describe a technical project you have worked on."]

    # Ask the user to upload a resume again in this section (Fixes the missing `pdf_file` error)
    pdf_file_ai = st.file_uploader("Upload Resume for AI Interview (PDF)", type=["pdf"])

    if candidate_name:
        if pdf_file_ai:
            resume_text = pdf_to_text(pdf_file_ai)  # Extract text
            resume_text = clean_text(resume_text)   # Clean extracted text

            if resume_text:
                resume_skills = generate_questions(resume_text)
                total_score = 0

                with st.form("ai_interview_form"):
                    answers = {}  # Store answers
                    
                    for question in resume_skills:
                        st.write("💬", question)
                        answers[question] = st.text_area(f"Your Answer ({question[:20]}...)", key=hash(question))

                    submit = st.form_submit_button("Submit Answers")
                    
                    if submit:
                        for question, answer in answers.items():
                            score = random.randint(1, 10)  # Assign a random score
                            total_score += score
                            st.session_state.leaderboard.append({"Name": candidate_name, "Score": score})

                        st.success(f"🎯 Total Score: {total_score}/{10 * len(resume_skills)}")
            else:
                st.warning("⚠️ Resume text extraction failed. Try again.")
        else:
            st.warning("⚠️ Please upload a resume for analysis.")

# ----------------------------------------------------------- LEADERBOARD -------------------------------------------------------------------
if page == "Leaderboard":
    st.header("🏆 Candidate Leaderboard")

    if "leaderboard" in st.session_state and st.session_state.leaderboard:
        df_leaderboard = pd.DataFrame(st.session_state.leaderboard)
        leaderboard_table = df_leaderboard.groupby("Name")["Score"].sum().reset_index()
        leaderboard_table = leaderboard_table.sort_values(by="Score", ascending=False)
        st.dataframe(leaderboard_table)
    else:
        st.write("🏅 No candidates ranked yet.")

# ----------------------------------------------------------- DATABASE RECORDS -------------------------------------------------------------------
if page == "Database Records":
    st.header("📂 Database Records")

    df = fetch_resume_data()
    if not df.empty:
        st.dataframe(df)
        category = st.selectbox("Select Category", df["Category"].unique())
        if category:
            filtered_df = df[df["Category"] == category]
            st.dataframe(filtered_df)
    else:
        st.write("🚫 No data found in the database.")
