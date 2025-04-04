import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import logging

def create_vector_store(directory, vector_store_path):
    total_characters = 0
    total_csvs = 0
    all_documents = []

    for filename in tqdm(os.listdir(directory)):
        if filename.endswith(".csv"):
            total_csvs += 1
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)

            for index, row in df.iterrows():
                clause_name = row['clause_name']
                clause_desc = row['clause_desc']
                clause_type = row['clause_type']
                document_type = row['document_type']

                doc_content = f"Clause Name: {clause_name}\nClause Description: {clause_desc}\nClause Type: {clause_type}\nDocument Type: {document_type}"
                document = Document(
                    page_content=doc_content,
                    metadata={"source": filename, "page": 1, "document_type": document_type, "clause_name": clause_name}  
                )
                all_documents.append(document)
                total_characters += len(doc_content)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=128000,
        chunk_overlap=200,
        add_start_index=True,
    )
    split_documents = text_splitter.split_documents(all_documents)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if os.path.exists(vector_store_path):
        vector_store = FAISS.load_local(
            vector_store_path, embeddings, allow_dangerous_deserialization=True
        )
    else:
        vector_store = FAISS.from_documents(split_documents, embeddings)

    document_ids = vector_store.add_documents(documents=split_documents)

    vector_store.save_local(vector_store_path)

    return (
        vector_store,
        total_characters,
        total_csvs,
        split_documents,
        len(document_ids),
    )

def load_vector_store(vector_store_path):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)

def find_document_type(vector_store, text):
    # logging.debug(f"Searching for document type with text: {text[:500]}...") 
    results = vector_store.similarity_search(text, k=100)
    # logging.debug(f"Search results: {results}")
    if results:
        document_type = results[0].metadata.get("document_type", "Unknown")
        clause_names = list(set(result.metadata.get("clause_name", "Unknown") for result in results))
        # logging.debug(f"Found document type: {document_type} with clause names: {clause_names}")
        return document_type, clause_names
    return "Unknown", []