import os
from flask import Flask, render_template, request
from create_vector_store import create_vector_store

app = Flask(__name__)

documents_dir = os.path.join(os.path.dirname(__file__), "documents")
vector_store_path = os.path.join(os.path.dirname(__file__), "vector_store")

vector_store, total_characters, total_csvs, split_documents, total_documents = create_vector_store(documents_dir, vector_store_path)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print(f"Total number of CSVs present: {total_csvs}")
    print(f"Total number of split documents: {len(split_documents)}")
    print(f"Total number of split documents stored: {total_documents}")
    app.run(debug=True)
