from dotenv import load_dotenv
import os
import csv
import mysql.connector

# Load environment variables
load_dotenv()
print(os.getenv('DB_PASSWORD'))
# Database configuration from .env file
db_config = {
    'host': os.getenv('DB_HOST', "localhost"),
    'user': os.getenv('DB_USER', "root"),
    'passwd': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'allow_local_infile': True
}

def create_db_connection(db_config):
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_table_from_csv(connection, csv_file_path, table_name):
    cursor = connection.cursor()

    # Read the CSV file to get column names
    with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        columns = next(reader)  # Assuming first row has column names

    # Define column types - assuming all float except for specified columns
    column_types = ', '.join([f"`{col}` FLOAT" if col not in ("Date", "Location", "Test_ID", "Name") else f"`{col}` TEXT" for col in columns])

    # Create table SQL statement
    create_table_statement = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({column_types});"
    cursor.execute(create_table_statement)

    # Import CSV data into MySQL table
    load_data_statement = f"""
    LOAD DATA LOCAL INFILE '{csv_file_path}'
    INTO TABLE {table_name}
    FIELDS TERMINATED BY ',' 
    ENCLOSED BY '"' 
    LINES TERMINATED BY '\\n'
    IGNORE 1 ROWS;
    """
    cursor.execute(load_data_statement)

    # Update type of Date column to DATE
    date_update_query = f"UPDATE `{table_name}` SET Date = STR_TO_DATE(Date, '%d/%m/%Y')"
    cursor.execute(date_update_query)
    date_update_query = f"ALTER TABLE `{table_name}` MODIFY COLUMN Date DATE"
    cursor.execute(date_update_query)

    connection.commit()
    cursor.close()

def main():
    db_connection = create_db_connection(db_config)
    if db_connection:
        csv_file_path = 'test_results.csv'
        table_name = 'test_results'
        create_table_from_csv(db_connection, csv_file_path, table_name)
        db_connection.close()
    else:
        print("Failed to connect to database.")

if __name__ == "__main__":
    main()
