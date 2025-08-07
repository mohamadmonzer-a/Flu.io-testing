from fastapi import FastAPI, HTTPException
import os
import requests
from supabase import create_client

app = FastAPI()

# Load env variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "pdf-files"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_bucket_if_not_exists():
    buckets = supabase.storage.get_buckets()
    existing = [b["name"] for b in buckets]
    if BUCKET_NAME not in existing:
        supabase.storage.create_bucket(BUCKET_NAME)

@app.get("/")
def health():
    return {"message": "🚀 FastAPI app is running on Fly.io"}

@app.post("/import-pdf")
def import_pdf():
    pdf_url = "https://raw.githubusercontent.com/mohamadmonzer-a/Flu.io-testing/main/pdf-to-embed/Final_amended_after_printing_EN_PHC_Guide_September_25_2c_2015.pdf"
    local_path = "/tmp/temp.pdf"
    filename = "PHC_Guide.pdf"

    create_bucket_if_not_exists()

    # Download the PDF from GitHub
    r = requests.get(pdf_url)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="❌ Failed to download PDF")

    with open(local_path, "wb") as f:
        f.write(r.content)

    # Upload to Supabase Storage
    with open(local_path, "rb") as f:
        data = f.read()

    res = supabase.storage.from_(BUCKET_NAME).upload(filename, data, {"upsert": True})

    if res.get("error"):
        raise HTTPException(status_code=500, detail=f"❌ Upload failed: {res['error']}")

    return {"message": f"✅ Uploaded {filename} to Supabase bucket '{BUCKET_NAME}'"}
