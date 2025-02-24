import os
from flask import Flask, render_template, request, redirect, url_for
from vector_store import create_vector_store, load_vector_store, find_document_type
from PyPDF2 import PdfReader
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

documents_dir = os.path.join(os.path.dirname(__file__), "documents")
vector_store_path = os.path.join(os.path.dirname(__file__), "vector_store")

# vector_store, total_characters, total_csvs, split_documents, total_documents = create_vector_store(documents_dir, vector_store_path)

vector_store = load_vector_store(vector_store_path)

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
        document_type, clause_names = find_document_type(vector_store, pdf_text)
        
        return redirect(url_for('index', document_type=document_type, clause_names=clause_names))
    
    return redirect(url_for('index'))

def extract_text_from_pdf(file_path):
    pdf_text = ""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            pdf_text += page.extract_text()
    return pdf_text

if __name__ == '__main__':
    app.run(debug=True)