import pymysql
import pandas as pd

# Database connection details
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "SAnia@2004"
DB_NAME = "resume_db"

# Connect to MySQL database
try:
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = connection.cursor()

    # Read the processed CSV file
    df = pd.read_csv("processed_resume_data.csv")
    df.fillna('', inplace=True)  # Handle missing values

    # Check if necessary columns exist
    required_columns = {'Resume_str', 'Category', 'Cleaned_Resume', 'Entities'}
    missing_columns = required_columns - set(df.columns)
    
    if missing_columns:
        raise ValueError(f"❌ Missing required columns in CSV: {missing_columns}")

    # Convert 'Entities' column to string format (since MySQL does not support dictionary storage)
    df['Entities'] = df['Entities'].astype(str)

    # SQL Insert Query
    sql = """
    INSERT INTO resume_data (Resume_str, Category, Cleaned_Resume, Entities) 
    VALUES (%s, %s, %s, %s)
    """

    # Insert each row into MySQL
    for _, row in df.iterrows():
        cursor.execute(sql, (row['Resume_str'], row['Category'], row['Cleaned_Resume'], row['Entities']))

    # Commit and close the connection
    connection.commit()
    cursor.close()
    connection.close()

    print("✅ Resume data successfully inserted into MySQL database.")

except pymysql.MySQLError as e:
    print(f"❌ MySQL Error: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
