# Health Test Data Extraction and Analysis

This project streamlines the extraction of clinical test results from PDF documents, processes the data with OpenAI's GPT model to identify and extract specific test values, stores the results in a MySQL database, and allows users to interactively query the data using natural language questions. It's designed to enhance accessibility and analysis of medical test data for healthcare professionals and researchers.

## Features

- **PDF Text Extraction**: Automatically extracts text from PDF documents containing clinical test results.
- **Data Processing with OpenAI**: Utilizes OpenAI's powerful GPT model to identify and extract specific test results from the unstructured text data.
- **Data Storage**: Processes and stores the extracted data in a structured MySQL database format for easy access and analysis.
- **Dynamic Configuration**: Easy updates without code changes through external configuration files for tests of interest and database schema mappings.
- **Interactive Data Queries**: Ability to ask questions in natural language about the data, with the system generating SQL queries, executing them, and returning results.

## Getting Started

### Prerequisites

- Python 3.8+
- MySQL Server
- OpenAI API Key
- Required Python packages: `pdfplumber`, `openai`, `mysql-connector-python`, `python-dotenv`

### Installation

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/gauri-nagavkar/Talk_with_your_data.git
    ```

2. Navigate to the project directory:

    ```bash
    cd Talk_with_your_data
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up your `.env` file with the necessary environment variables:

    ```plaintext
    OPENAI_API_KEY=your_openai_api_key_here
    DB_HOST=localhost
    DB_USER=your_database_user
    DB_PASSWORD=your_database_password
    DB_NAME=your_database_name
    ```

5. Adjust the `tests_of_interest.txt` and `data_mapping.json` files to match your specific requirements.

### Usage

1. To insert the results from your pdf file into the database, run the following command, followed by the path to your pdf file:

    ```bash
    python read_insert.py
    ```

2. To talk with your data, run the `answer_questions.py` file followed by your question.

## Configuration

- **Tests of Interest**: Update `tests_of_interest.txt` to modify or add new tests to be extracted.
- **Database Mapping**: Adjust `data_mapping.json` to map extracted test names to your database column names.

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, and suggest features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT model used for data extraction and processing.
- The developers of `pdfplumber`, `mysql-connector-python`, and `python-dotenv` for their excellent Python packages.

