import requests
import io
import fitz  # PyMuPDF
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def embed_pdf(url):
    res = requests.get(url)
    pdf = fitz.open(stream=io.BytesIO(res.content), filetype="pdf")
    text = "\n".join([page.get_text() for page in pdf])

    embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8191]  # safe truncation
    )

    return {
        "source_url": url,
        "text": text[:1000],  # Optional preview
        "embedding": embedding.data[0].embedding
    }
