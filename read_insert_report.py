import os
import pdfplumber
import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def read_tests_of_interest(file_path='tests_of_interest.txt'):
    """Reads tests of interest from a file."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def read_data_mapping(file_path='data_mapping.json'):
    """Reads data mapping from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def initialize_openai_client():
    """Initializes and returns the OpenAI client configured with an API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key,)

def extract_values_with_openai(client, pdf_text, tests_of_interest):
    """Uses OpenAI to extract specific values from text."""
    user_message = f"""
    I have a list of blood tests from a PDF document, and I need to extract the values for specific tests. 
    The document's text has been extracted and is provided below. 
    Please review the text and list the values for the following tests in JSON format. 
    If a test's value is not found, please mark it with "-". Also include the date of the test in the JSON.
    The tests of interest are: {', '.join(tests_of_interest)}. 
    Note: Provide only the values, excluding units or percentage signs. If there are multiple instances of the same test, create multiple JSONs, where one JSON contains all the tests done on one day.
    Here's the extracted text: {pdf_text}
    """

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        temperature=0.3,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
        )
    return response.choices[0].message.content

def parse_json_from_response(response_content):
    """Parses JSON objects from the OpenAI response content."""
    json_str = response_content.replace('json\n', '').replace('```', '')
    json_objects = [obj.strip() for obj in json_str.split('},')]
    jsons = []

    for j in json_objects:
        corrected_str = "{" + j.strip('[]').strip().strip('{}').strip().strip('```}').strip().strip(']').strip().strip('}') + "}"
        jsons.append(json.loads(corrected_str))
    
    return jsons

def preprocess_data_for_insertion(json_data, mapping):
    """Preprocesses JSON data for database insertion using the provided mapping."""
    processed_data = []
    for data in json_data:
        # print(data)
        record = {}
        for key, value in data.items():
            # print(key,value)
            db_column = mapping.get(key, key)
            # print(db_column)
            if str.lower(key) == "date":
                record["Date"] = convert_to_yyyy_mm_dd(value)
            else:
                record[db_column] = None if value == "-" else float(value.replace(',', ''))
        processed_data.append(record)
    return processed_data

def convert_to_yyyy_mm_dd(date_str):
    """Converts dates to the YYYY-MM-DD format."""
    for fmt in ("%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def insert_data_into_database(data, Name, Location, Test_ID):
    """Inserts processed data into the database."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        for record in data:
            columns = ', '.join(record.keys()) + ", Name, Location, Test_ID"
            values = list(record.values()) + [Name, Location, Test_ID]
            placeholders = ', '.join('%s' for _ in values)  

            sql = f"INSERT INTO test_results ({columns}) VALUES ({placeholders})"
            
            # Debugging: Print SQL and values to check alignment
            # print("SQL Command:", sql)
            # print("Values:", values)

            try:
                cursor.execute(sql, values)
                print("Inserted")
            except Exception as e:
                print("Error executing SQL:", e)
        conn.commit()
    except Error as e:
        print(f"Database error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def main():
    Name = input("What's the patient's name?: ")
    Location = input("What's the Location of tests?: ")
    Test_ID = input("What's the Test ID?: ")
    tests_of_interest = read_tests_of_interest()
    mapping = read_data_mapping()
    pdf_text = extract_text_from_pdf("Health_summary.PDF")
    client = initialize_openai_client()
    extracted_values = extract_values_with_openai(client, pdf_text, tests_of_interest)
    json_data = parse_json_from_response(extracted_values)
    processed_data = preprocess_data_for_insertion(json_data, mapping)
    insert_data_into_database(processed_data, Name, Location, Test_ID)
    print("Insertion process completed successfully.")

if __name__ == "__main__":
    main()
