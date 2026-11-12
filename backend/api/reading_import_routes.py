"""Content extraction for the standalone reading flow; no Main Assistant UI changes."""
import ipaddress
import socket
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from backend.api.auth_routes import get_current_user

router = APIRouter(prefix="/api/v2/german-reading/import", tags=["reading"])

class UrlImport(BaseModel):
    url: str = Field(min_length=8, max_length=2048)

def extract_url(url):
    # Check every redirect before fetching, including DNS-resolved private hosts.
    for _ in range(5):
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Provide a public HTTP or HTTPS article URL.")
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("Only public article URLs are supported.")
        with requests.get(url, timeout=(5, 20), allow_redirects=False, stream=True) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers.get("Location", ""))
                continue
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", ""):
                raise ValueError("The URL must point to an HTML article.")
            chunks, length = [], 0
            for chunk in response.iter_content(65536):
                length += len(chunk)
                if length > 2 * 1024 * 1024:
                    raise ValueError("The webpage is too large. Paste a short passage instead.")
                chunks.append(chunk)
        soup = BeautifulSoup(b"".join(chunks), "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Web article"
        for item in soup(["script", "style", "nav", "footer", "header", "aside"]):
            item.decompose()
        article = soup.find("article") or soup.find("main") or soup.body or soup
        text = "\n".join(p.get_text(" ", strip=True) for p in article.find_all(["p", "h1", "h2", "h3", "li"]))
        return {"text": text.strip(), "title": title[:80]}
    raise ValueError("Too many redirects. Paste the article text instead.")

@router.post("/url")
async def import_url(payload: UrlImport):
    try:
        return await run_in_threadpool(extract_url, payload.url)
    except (ValueError, requests.RequestException, OSError) as error:
        raise HTTPException(422, str(error) if isinstance(error, ValueError) else "Unable to fetch this article. Paste its text instead.")

@router.post("/file")
async def import_file(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(422, "Choose a PDF file.")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Choose a PDF smaller than 10 MB.")
    from backend.preprocessing.pdf_extractor import extract_text_from_pdf_bytes
    text = await run_in_threadpool(extract_text_from_pdf_bytes, content)
    if not text.strip():
        raise HTTPException(422, "No readable text found. Scanned PDFs require text recognition; paste the text instead.")
    return {"text": text, "title": file.filename}

