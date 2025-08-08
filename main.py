import os
import io
import json
import hashlib
import psycopg2
import fitz  # PyMuPDF
from fastapi import FastAPI, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Environment variables
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
GOOGLE_SERVICE_ACCOUNT_JSON = "google_service_account.json"  # We'll write this from base64 secret
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1NK0MlcLuvSDgxphWurQfMLXCaYAIK1N6")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_SERVICE_ACCOUNT_B64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_B64", None)

def write_gsa_file():
    if GOOGLE_SERVICE_ACCOUNT_B64:
        import base64
        with open(GOOGLE_SERVICE_ACCOUNT_JSON, "wb") as f:
            f.write(base64.b64decode(GOOGLE_SERVICE_ACCOUNT_B64))
        print("Google Service Account JSON written from base64 env.")

write_gsa_file()

# Connect to Supabase Postgres
conn = psycopg2.connect(SUPABASE_DB_URL)
conn.autocommit = True
cur = conn.cursor()

# Prepare OpenAI embedder
embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, embedding_model_name="text-embedding-3-small")

# Setup Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def list_pdfs_in_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def download_pdf(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()

def insert_pdf_embedding(content_text, metadata, file_name, chunk_index):
    content_hash = hashlib.sha256(content_text.encode()).hexdigest()
    cur.execute("SELECT 1 FROM pdf WHERE content_hash = %s", (content_hash,))
    if cur.fetchone():
        print(f"Skipping duplicate chunk {chunk_index}")
        return
    embedding = embedder.embed_query(content_text)
    message = {"chunk_index": chunk_index, "source": metadata.get("source")}
    cur.execute("""
        INSERT INTO pdf (session_id, content, content_hash, message, embedding, metadata, file_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (None, content_text, content_hash, json.dumps(message), embedding, json.dumps(metadata), file_name))
    print(f"Inserted chunk {chunk_index}")

def extract_and_embed_pdf(pdf_bytes, file_name):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunk_index = 0
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            metadata = {"page": page_num, "source": file_name}
            insert_pdf_embedding(text, metadata, file_name, chunk_index)
            chunk_index += 1

@app.post("/embed-pdfs")
async def embed_pdfs():
    try:
        pdf_files = list_pdfs_in_folder(GOOGLE_DRIVE_FOLDER_ID)
        if not pdf_files:
            return {"message": "No PDFs found in Google Drive folder."}
        for idx, pdf_file in enumerate(pdf_files):
            print(f"Downloading {pdf_file['name']}...")
            pdf_bytes = download_pdf(pdf_file['id'])
            print(f"Embedding content of {pdf_file['name']}...")
            extract_and_embed_pdf(pdf_bytes, pdf_file['name'])
        return {"message": f"Successfully embedded {len(pdf_files)} PDFs."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
