from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def save_embedding(data):
    supabase.table("pdf_embeddings").insert({
        "source_url": data["source_url"],
        "text_snippet": data["text"],
        "embedding": data["embedding"]
    }).execute()
