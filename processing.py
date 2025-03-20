import pandas as pd
import re
import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the dataset
file_path = "C:\\Users\\SANIA\\Downloads\\Resume.csv"  # Change this if needed
df = pd.read_csv(file_path)

# Remove unnecessary columns
df = df.drop(columns=["ID", "Resume_html"], errors="ignore")

# Remove duplicates
df = df.drop_duplicates()

# Initialize NLP tools
nltk.download('punkt')  # Ensure 'punkt' is downloaded properly
nltk.download('stopwords')  
nltk.download('wordnet')
nlp = spacy.load("en_core_web_sm")

stop_words = set(nltk.corpus.stopwords.words("english"))
lemmatizer = nltk.WordNetLemmatizer()

# Advanced text preprocessing function
def preprocess_text_advanced(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\W+', ' ', text)  # Remove special characters
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = text.strip()  # Remove extra spaces

    words = nltk.word_tokenize(text)  # Tokenization
    words = [word for word in words if word not in stop_words]  # Stopword removal
    words = [lemmatizer.lemmatize(word) for word in words]  # Lemmatization
    return " ".join(words)

# Apply advanced text preprocessing
df["Cleaned_Resume"] = df["Resume_str"].astype(str).apply(preprocess_text_advanced)

# Named Entity Recognition (NER) to extract skills, names, etc.
def extract_entities(text):
    doc = nlp(text)
    entities = {ent.label_: ent.text for ent in doc.ents}
    return entities

df["Entities"] = df["Cleaned_Resume"].apply(extract_entities)

# TF-IDF Feature Extraction
vectorizer = TfidfVectorizer(max_features=1000)  # Limit to top 1000 features
X = vectorizer.fit_transform(df["Cleaned_Resume"])

# Save the cleaned dataset
df.to_csv("Advanced_Cleaned_Resume.csv", index=False)

print("✅ Advanced resume preprocessing completed. Cleaned data saved as 'Advanced_Cleaned_Resume.csv'.")

