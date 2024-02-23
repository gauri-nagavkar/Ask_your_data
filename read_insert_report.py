import pdfplumber
from openai import OpenAI
import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Path to your PDF file
# pdf_path = "Report.pdf"
pdf_path = "Health_summary.PDF"

# Extract text from the PDF
pdf_text = extract_text_from_pdf(pdf_path)

# Print extracted text (for debugging purposes)
# print(pdf_text)


tests_of_interest = ["Glucose Fasting", "Blood Urea Nitrogen", "Creatinine", "Uric Acid", "Calcium", "Phosphorous",
    "Sodium", "Potassium", "Chloride", "Bilirubin-Total", "Bilirubin-Direct", "Bilirubin-Indirect",
    "Total Protein", "Albumin", "Globulin", "A/G Ratio", "SGPT (ALT)", "SGOT (AST)", "Haemoglobin",
    "Erythrocyte Count", "PCV (Packed Cell Volume)", "MCV (Mean Corpuscular Volume)", "MCH (Mean Corpuscular Hb)",
    "MCHC (Mean Corpuscular Hb Concn.)", "RDW (Red Cell Distribution Width)", "Total Leucocytes (WBC) count",
    "Absolute Neutrophils Count", "Absolute Lymphocyte Count", "Absolute Monocyte Count", "Absolute Eosinophil Count",
    "Absolute Basophil Count", "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils",
    "Platelet count", "MPV (Mean Platelet Volume)", "PCT ( Platelet crit)", "PDW (Platelet Distribution Width)",
    "ESR - Erythrocyte Sedimentation Rate", "HbA1C- Glycated Haemoglobin", "Estimated Average Glucose (eAG)",
    "Cholesterol-Total", "Triglycerides level", "HDL Cholesterol", "Non HDL Cholesterol", "LDL Cholesterol",
    "VLDL Cholesterol", "LDL/HDL RATIO", "CHOL/HDL RATIO", "Alkaline Phosphatase", "Gamma GT (GGTP)",
    "LDH-Lactate Dehydrogenase", "CPK-Creatinine Phospho Kinase", "Vitamin B12 level", "TSH(Ultrasensitive)",
    "Free T4", "Free T3", "25 Hydroxy (OH) Vit D", "AMH Mullerian Inhibiting Substance"]

def initialize_openai_client():
    return OpenAI(api_key="sk-c4pkpBvrwcq2nx9cvxfsT3BlbkFJdKKQrXfkjhsdkfhsd;lfjdslkgfsklghsdflkdsjfls;dhfs8BQpDL6Xh")

user_message = f"""
I have a list of blood tests from a PDF document, and I need to extract the values for specific tests. 
The document's text has been extracted and is provided below. 
Please review the text and list the values for the following tests in JSON format readable in python. 
If a test's value is not found, please mark it with "-". Also include the date of test in the JSON.
The tests of interest are:  {tests_of_interest}. 
Note: Provide only the values, excluding units or percentage signs. If there are multiple instances of the same test, create multiple jsons, where one json contains all the tests done on one day.
Here's the extracted text: {pdf_text}
"""

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user",
        "content":  user_message
    }
]


client = initialize_openai_client()

response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=messages,
  temperature=0.3,
  top_p=1.0,
  frequency_penalty=0,
  presence_penalty=0
)

print("Values extracted.")

try:
    # Extracting message directly from the completion response
    response_content = response.choices[0].message.content

    json_str = response_content.replace('json\n', '').replace('```', '')

    json_objects = [obj.strip() for obj in json_str.split('},')]

    jsons = []
    for j in json_objects:
        # print(j)
        a = j.strip('[]').strip().strip('{}').strip().strip('```}').strip().strip(']').strip().strip('}')
        # print(a)
        b = "{" + a + "}"
        # print("b: ", b)
        c = json.loads(b)
        jsons.append(c)

except Exception as e:
    print(f"Error extracting or parsing JSON: {e}")


# convert date to "yyyy-mm-dd" format 
def convert_to_yyyy_mm_dd(date_str):
    # Define possible date formats
    date_formats = [
        "%m-%d-%Y", "%m/%d/%Y",  # mm-dd-yyyy and mm/dd/yyyy
        "%d-%m-%Y", "%d/%m/%Y",  # dd-mm-yyyy and dd/mm/yyyy
    ]
    
    for fmt in date_formats:
        try:
            # Try to parse the date
            dt = datetime.strptime(date_str, fmt)
            # If parsing is successful, convert to standard format and return
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            # If parsing fails, try the next format
            continue
    # If all formats fail, return None or raise an exception
    return None


# Convert "-" to None
for data in jsons:
    # print(data)
    for k,v in data.items():
        if v == "-":
            data[k] = None
        elif k not in ("Date"):
            data[k] = float(v)


# Database connection parameters
db_config = {"host": "localhost", "user": "root", "password": "sgdfjgsdfjhg", "database": "bloodtests"}

connection = mysql.connector.connect(**db_config)
cursor = connection.cursor(prepared=True)

for data in jsons:
    # Corrected data dictionary with column names matching the SQL table
    corrected_data = {
    "Date": convert_to_yyyy_mm_dd(data.get("Date")),
    "Glucose_Fasting": data.get("Glucose Fasting"),
    "Blood_Urea_Nitrogen": data.get("Blood Urea Nitrogen"),
    "Creatinine": data.get("Creatinine"),
    "Uric_Acid": data.get("Uric Acid"),
    "Calcium": data.get("Calcium"),
    "Phosphorous": data.get("Phosphorous"),
    "Sodium": data.get("Sodium"),
    "Potassium": data.get("Potassium"),
    "Chloride": data.get("Chloride"),
    "Bilirubin_Total": data.get("Bilirubin-Total"),
    "Bilirubin_Direct": data.get("Bilirubin-Direct"),
    "BilirubinIn_direct": data.get("Bilirubin-Indirect"), # Adjust the JSON key to match SQL column name
    "Total_Protein": data.get("Total Protein"),
    "Albumin": data.get("Albumin"),
    "Globulin": data.get("Globulin"),
    "AG_Ratio": data.get("A/G Ratio"),
    "SGPT_ALT": data.get("SGPT (ALT)"),
    "SGOT_AST": data.get("SGOT (AST)"),
    "Haemoglobin": data.get("Haemoglobin"),
    "Erythrocyte_Count": data.get("Erythrocyte Count"),
    "PCV_Packed_Cell_Volume": data.get("PCV (Packed Cell Volume)"),
    "MCV_Mean_Corpuscular_Volume": data.get("MCV (Mean Corpuscular Volume)"),
    "MCH_Mean_Corpuscular_Hb": data.get("MCH (Mean Corpuscular Hb)"),
    "MCHC_Mean_Corpuscular_Hb_Concn": data.get("MCHC (Mean Corpuscular Hb Concn.)"),
    "RDW_Red_Cell_Distribution_Width": data.get("RDW (Red Cell Distribution Width)"),
    "Total_Leucocytes_WBC_count": data.get("Total Leucocytes (WBC) count"),
    "Absolute_Neutrophils_Count": data.get("Absolute Neutrophils Count"),
    "Absolute_Lymphocyte_Count": data.get("Absolute Lymphocyte Count"),
    "Absolute_Monocyte_Count": data.get("Absolute Monocyte Count"),
    "Absolute_Eosinophil_Count": data.get("Absolute Eosinophil Count"),
    "Absolute_Basophil_Count": data.get("Absolute Basophil Count"),
    "Neutrophils": data.get("Neutrophils"),
    "Lymphocytes": data.get("Lymphocytes"),
    "Monocytes": data.get("Monocytes"),
    "Eosinophils": data.get("Eosinophils"),
    "Basophils": data.get("Basophils"),
    "Platelet_Count": data.get("Platelet count"),
    "MPV_Mean_Platelet_Volume": data.get("MPV (Mean Platelet Volume)"),
    "PCT_Platelet_crit": data.get("PCT (Platelet crit)"),
    "PDW_Platelet_Distribution_Width": data.get("PDW (Platelet Distribution Width)"),
    "ESR_Erythrocyte_Sedimentation_Rate": data.get("ESR - Erythrocyte Sedimentation Rate"),
    "HbA1C_Glycated_Haemoglobin": data.get("HbA1C- Glycated Haemoglobin"),
    "Estimated_Average_Glucose_eAG": data.get("Estimated Average Glucose (eAG)"),
    "Cholesterol_Total": data.get("Cholesterol-Total"),
    "Triglycerides_level": data.get("Triglycerides level"),
    "HDL_Cholesterol": data.get("HDL Cholesterol"),
    "Non_HDL_Cholesterol": data.get("Non HDL Cholesterol"),
    "LDL_Cholesterol": data.get("LDL Cholesterol"),
    "VLDL_Cholesterol": data.get("VLDL Cholesterol"),
    "LDL_HDL_RATIO": data.get("LDL/HDL RATIO"),
    "CHOL_HDL_RATIO": data.get("CHOL/HDL RATIO"),
    "Alkaline_Phosphatase": data.get("Alkaline Phosphatase"),
    "Gamma_GT_GGTP": data.get("Gamma GT (GGTP)"), 
    "LDH_Lactate_Dehydrogenase": data.get("LDH-Lactate Dehydrogenase"), 
    "CPK_Creatinine_Phospho_Kinase": data.get("CPK-Creatinine Phospho Kinase"),
    "Vitamin_B12_level": data.get("Vitamin B12 level"),
    "TSH_Ultrasensitive": data.get("TSH(Ultrasensitive)"),
    "Free_T4": data.get("Free T4"),
    "Free_T3": data.get("Free T3"),
    "25_Hydroxy_Vit_D": data.get("25 Hydroxy (OH) Vit D"),
    "AMH_Mullerian_Inhibiting_Substance": data.get("AMH Mullerian Inhibiting Substance")
    }

    # Corrected SQL INSERT statement to use the correct placeholder format
    sql = '''
    INSERT INTO test_results 
    (Date, Location, Glucose_Fasting, Blood_Urea_Nitrogen, Creatinine, Uric_Acid, Calcium, Phosphorous, Sodium, Potassium, Chloride, Bilirubin_Total, Bilirubin_Direct, Bilirubin_Indirect, Total_Protein, Albumin, Globulin, AG_Ratio, SGPT_ALT, SGOT_AST, Haemoglobin, Erythrocyte_Count, PCV_Packed_Cell_Volume, MCV_Mean_Corpuscular_Volume, MCH_Mean_Corpuscular_Hb, MCHC_Mean_Corpuscular_Hb_Concn, RDW_Red_Cell_Distribution_Width, Total_Leucocytes_WBC_count, Absolute_Neutrophils_Count, Absolute_Lymphocyte_Count, Absolute_Monocyte_Count, Absolute_Eosinophil_Count, Absolute_Basophil_Count, Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils, Platelet_Count, MPV_Mean_Platelet_Volume, PCT_Platelet_crit, PDW_Platelet_Distribution_Width, ESR_Erythrocyte_Sedimentation_Rate, HbA1C_Glycated_Haemoglobin, Estimated_Average_Glucose_eAG, Cholesterol_Total, Triglycerides_level, HDL_Cholesterol, Non_HDL_Cholesterol, LDL_Cholesterol, VLDL_Cholesterol, LDL_HDL_RATIO, CHOL_HDL_RATIO, Alkaline_Phosphatase, Gamma_GT_GGTP, LDH_Lactate_Dehydrogenase, CPK_Creatinine_Phospho_Kinase, Vitamin_B12_level, TSH_Ultrasensitive, Free_T4, Free_T3, 25_Hydroxy_Vit_D, AMH_Mullerian_Inhibiting_Substance) 
    VALUES (%(Date)s, 'Santa Clara', %(Glucose_Fasting)s, %(Blood_Urea_Nitrogen)s, %(Creatinine)s, %(Uric_Acid)s, %(Calcium)s, %(Phosphorous)s, %(Sodium)s, %(Potassium)s, %(Chloride)s, %(Bilirubin_Total)s, %(Bilirubin_Direct)s, %(BilirubinIn_direct)s, %(Total_Protein)s, %(Albumin)s, %(Globulin)s, %(AG_Ratio)s, %(SGPT_ALT)s, %(SGOT_AST)s, %(Haemoglobin)s, %(Erythrocyte_Count)s, %(PCV_Packed_Cell_Volume)s, %(MCV_Mean_Corpuscular_Volume)s, %(MCH_Mean_Corpuscular_Hb)s, %(MCHC_Mean_Corpuscular_Hb_Concn)s, %(RDW_Red_Cell_Distribution_Width)s, %(Total_Leucocytes_WBC_count)s, %(Absolute_Neutrophils_Count)s, %(Absolute_Lymphocyte_Count)s, %(Absolute_Monocyte_Count)s, %(Absolute_Eosinophil_Count)s, %(Absolute_Basophil_Count)s, %(Neutrophils)s, %(Lymphocytes)s, %(Monocytes)s, %(Eosinophils)s, %(Basophils)s, %(Platelet_Count)s, %(MPV_Mean_Platelet_Volume)s, %(PCT_Platelet_crit)s, %(PDW_Platelet_Distribution_Width)s, %(ESR_Erythrocyte_Sedimentation_Rate)s, %(HbA1C_Glycated_Haemoglobin)s, %(Estimated_Average_Glucose_eAG)s, %(Cholesterol_Total)s, %(Triglycerides_level)s, %(HDL_Cholesterol)s, %(Non_HDL_Cholesterol)s, %(LDL_Cholesterol)s, %(VLDL_Cholesterol)s, %(LDL_HDL_RATIO)s, %(CHOL_HDL_RATIO)s, %(Alkaline_Phosphatase)s, NULL, NULL, NULL, %(Vitamin_B12_level)s, %(TSH_Ultrasensitive)s, %(Free_T4)s, %(Free_T3)s, %(25_Hydroxy_Vit_D)s, NULL)
    '''
    # Viewing the query before execution
    query_preview = sql % corrected_data
    print("Query preview:", query_preview)


    cursor.execute(sql, corrected_data)
    connection.commit()

    print("Data inserted successfully.")


cursor.close()
connection.close()
print("MySQL connection is closed.")