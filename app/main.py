from app.drive import get_pdf_links
from app.embed import embed_pdf
from app.supabase import save_embedding

def main():
    pdf_urls = get_pdf_links()
    for url in pdf_urls:
        try:
            embedding_data = embed_pdf(url)
            save_embedding(embedding_data)
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")

if __name__ == "__main__":
    main()
