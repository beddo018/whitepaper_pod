import urllib.request as libreq
import urllib.parse as libparse
import xml.etree.ElementTree as ET
import logging
import ssl

logging.basicConfig(level=logging.DEBUG)

# Create SSL context that ignores certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def query(query_params):
    # Encode the query_params string to handle spaces and special characters
    encoded_params = libparse.quote(query_params, safe='=&')
    url = f'http://export.arxiv.org/api/query?{encoded_params}'
    
    # Create request with SSL context
    req = libreq.Request(url)
    with libreq.urlopen(req, context=ssl_context) as response:
        r = response.read()
    
    logging.debug(f"Response content: {r.decode('utf-8')}")
    
    root = ET.fromstring(r)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        # Extract the arXiv ID from the full URL
        arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text
        # Convert to the format expected by query_for_pdf
        paper_url = arxiv_id.replace('http://arxiv.org/abs/', 'http://arxiv.org/abs/')
        
        paper = {
            'id': arxiv_id,  # Full arXiv URL (e.g., http://arxiv.org/abs/1911.06612v1)
            'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
            'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text,  # Map summary to abstract
            'publishedDate': entry.find('{http://www.w3.org/2005/Atom}published').text,
            'authors': [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
            'journal': 'arXiv',  # arXiv papers don't have a journal, so we set this
            'url': paper_url,  # Add url field for frontend compatibility
            'pdf_url': next((link.attrib['href'] for link in entry.findall('{http://www.w3.org/2005/Atom}link') if 'type' in link.attrib and link.attrib['type'] == 'application/pdf'), None)
        }
        papers.append(paper)
    
    return papers

def query_for_pdf(paper_url):
    pdf_url = paper_url.replace('abs','pdf')
    print(pdf_url)
    try:
        # Create request with SSL context
        req = libreq.Request(pdf_url)
        with libreq.urlopen(req, context=ssl_context) as response:
            print(response.headers)
            # PDF files are binary, so we read them as bytes and return as string
            # We'll let the PDF processor handle the binary data
            pdf_content = response.read()
            # For now, return as string - the PDF processor should handle binary data
            return pdf_content
    except Exception as e:
        raise Exception(f"Failed to retrieve the PDF: {e}")
    
# if __name__ == "__main__":
#     content = query_for_pdf("http://arxiv.org/abs/1911.06612v1")
#     print("ARTICLE SUMMARY:\n~~~~~~~~\n")

#     print(f"String saved to {file_name}")
    
#     print("ARTICLE END:\n~~~~~~~~\n")