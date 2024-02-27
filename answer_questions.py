import os
import re
import mysql.connector
from mysql.connector import Error
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def initialize_openai_client():
    """Initializes and returns the OpenAI client configured with an API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key,)

def get_database_connection():
    """Creates and returns a database connection using environment variables."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'bloodtests')
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_table_description(cursor, table_name):
    """Fetches and returns the schema of the specified table."""
    try:
        cursor.execute(f"DESCRIBE `{table_name}`")
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching table description: {e}")
        return None

def create_message(test_table_name, normal_table_name, query_description, test_columns_description, normal_columns_description):
    """Constructs and returns a prompt message for the OpenAI API based on table descriptions."""
    test_columns = ', '.join([f"`{col[0]}` {col[1]}" for col in test_columns_description])
    normal_columns = ', '.join([f"`{col[0]}` {col[1]}" for col in normal_columns_description])
    system_message = (f"Here are two SQL tables. The first one, `{test_table_name}`, contains blood test values over the years."
                      f" The second one, `{normal_table_name}`, contains normal ranges for these tests."
                      " Your job is to write a SQL query based on a user request."
                      f" Test table schema: CREATE TABLE `{test_table_name}` ({test_columns});"
                      f" Normal values table schema: CREATE TABLE `{normal_table_name}` ({normal_columns});")
    user_message = f"User request: {query_description}"
    return {"system": system_message, "user": user_message}

def extract_sql_query(response_text):
    """Extracts an SQL query from the OpenAI response text."""
    match = re.search(r"```sql\n([\s\S]*?)\n```", response_text)
    return match.group(1).strip() if match else None

def is_read_only_query(query):
    """Checks if the SQL query is read-only."""
    return query.lower().strip().startswith('select')

def fetch_results_as_dataframe(conn, query):
    """Executes a read-only SQL query and returns the results as a pandas DataFrame."""
    try:
        return pd.read_sql_query(query, conn)
    except Error as e:
        print(f"Error executing query: {e}")
        return None

def generate_and_execute_query(client, conn, test_table_name='test_results', normal_table_name='normal_values'):
    """Generates an SQL query based on user input and executes it, displaying the results."""
    user_query = input("Please enter your query description: ")
    cursor = conn.cursor()

    test_columns_description = get_table_description(cursor, test_table_name)
    normal_columns_description = get_table_description(cursor, normal_table_name)

    if test_columns_description and normal_columns_description:
        prompt = create_message(test_table_name, normal_table_name, user_query, test_columns_description, normal_columns_description)
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": prompt["system"]}, {"role": "user", "content": prompt["user"]}],
            temperature=0,
            max_tokens=256,
        )

        sql_query = extract_sql_query(response.choices[0].message.content)
        if sql_query and is_read_only_query(sql_query):
            df = fetch_results_as_dataframe(conn, sql_query)
            if df is not None and not df.empty:
                print(df)
            else:
                print("No data returned or error occurred.")
        else:
            print("Generated query is not read-only or invalid. Execution aborted.")
    else:
        print("Failed to generate message due to missing table descriptions.")

    cursor.close()

def main():
    """Main function to orchestrate the query answering flow."""
    conn = get_database_connection()
    if conn:
        client = initialize_openai_client()
        generate_and_execute_query(client, conn)
        conn.close()
    else:
        print("Failed to initialize database connection or OpenAI client.")

if __name__ == "__main__":
    main()
