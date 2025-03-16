import os
from flask import Flask, render_template, request, redirect, url_for
from vector_store import create_vector_store, load_vector_store, find_document_type
from PyPDF2 import PdfReader
import logging
import yaml
from groq import Groq
import requests

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

documents_dir = os.path.join(os.path.dirname(__file__), "documents")
vector_store_path = os.path.join(os.path.dirname(__file__), "vector_store")

# vector_store, total_characters, total_csvs, split_documents, total_documents = create_vector_store(documents_dir, vector_store_path)

vector_store = load_vector_store(vector_store_path)

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

with open("prompt.txt", "r") as file:
    prompt = file.read()

groq_api_key = config["GROQ_API_KEY"]
model = "llama-3.3-70b-versatile"
groq_client = Groq(api_key=groq_api_key)

@app.route('/')
def index():
    document_type = request.args.get('document_type')
    clause_names = request.args.getlist('clause_names')
    return render_template('index.html', document_type=document_type, clause_names=clause_names)

@app.route('/upload', methods=['POST'])
def upload():
    if 'contract' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['contract']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(documents_dir, file.filename)
        file.save(file_path)
        pdf_text = extract_text_from_pdf(file_path)
        logging.debug(f"Extracted text from PDF: {pdf_text[:500]}...")  
        # document_type, clause_names = find_document_type(vector_store, pdf_text)
        document_type, clause_names = extract_document_info_with_groq(pdf_text)
        
        return redirect(url_for('index', document_type=document_type, clause_names=clause_names))
    
    return redirect(url_for('index'))

def extract_text_from_pdf(file_path):
    pdf_text = ""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            pdf_text += page.extract_text()
    return pdf_text

def extract_document_info_with_groq(pdf_text):
    prompt_text = f"""
    Based on the following contract text, extract:
    - The document type
    - A list of clause names take it from the document only. If and only if clause name is not present, give it a name from the vector store.

    Text:
    {pdf_text}

    Please provide the document type and clause names in this format:
    - Document Type: <document_type>
    - Clause Names: <clause_name_1>, <clause_name_2>, ...
    """

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model=model,
            stream=False
        )

        message_content = chat_completion.choices[0].message.content.strip()
        logging.debug(f"Full Response: {message_content}")

        document_type = ""
        clause_names = ""
        if "Document Type:" in message_content:
            start_idx = message_content.find("Document Type:") + len("Document Type:")
            end_idx = message_content.find("\n", start_idx)
            document_type = message_content[start_idx:end_idx].strip()

        if "Clause Names:" in message_content:
            start_idx = message_content.find("Clause Names:") + len("Clause Names:")
            clause_names_str = message_content[start_idx:].strip()
            clause_names = [clause.strip() for clause in clause_names_str.split(',')]

        logging.debug(f"Extracted Document Type: {document_type}")
        logging.debug(f"Extracted Clause Names: {clause_names}")

        return document_type, clause_names

    except Exception as e:
        logging.error(f"Error in Groq API call: {str(e)}")
        return 'Error', []


if __name__ == '__main__':
    app.run(debug=True)