import requests
from bs4 import BeautifulSoup

FOLDER_ID = "1NK0MlcLuvSDgxphWurQfMLXCaYAIK1N6"

def get_pdf_links():
    url = f"https://drive.google.com/embeddedfolderview?id={FOLDER_ID}#list"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and "file/d/" in href:
            file_id = href.split("/d/")[1].split("/")[0]
            direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            links.append(direct_link)
    return links
