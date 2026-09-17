import pandas as pd
from pypdf import PdfReader
from docx import Document
import io

def parse_structured_file(uploaded_file):
    """Parses and sanitizes any Excel sheet or CSV formatting instantly."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Drop rows that are entirely empty or columns with no header names
    df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
    
    # Strip annoying whitespace trailing characters from headers
    df.columns = df.columns.str.strip()
    return df

def parse_unstructured_file(uploaded_file):
    """Extracts raw text string blocks cleanly out of PDFs and Word documents."""
    text_content = ""
    
    if uploaded_file.name.endswith('.pdf'):
        pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content += extracted + "\n"
                
    elif uploaded_file.name.endswith('.docx'):
        doc = Document(io.BytesIO(uploaded_file.read()))
        for para in doc.paragraphs:
            text_content += para.text + "\n"
            
    return text_content.strip()