import urllib.request as libreq
import urllib.parse as libparse
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.DEBUG)

def query(query_params):
    encoded_params = libparse.quote(query_params)
    url = f'http://export.arxiv.org/api/query?{encoded_params}'
    
    with libreq.urlopen(url) as response:
        r = response.read()
    
    logging.debug(f"Response content: {r.decode('utf-8')}")
    
    root = ET.fromstring(r)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        paper = {
            'id': entry.find('{http://www.w3.org/2005/Atom}id').text,
            'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
            'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text,
            'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
            'authors': [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
            'pdf_url': next((link.attrib['href'] for link in entry.findall('{http://www.w3.org/2005/Atom}link') if 'type' in link.attrib and link.attrib['type'] == 'application/pdf'), None)
        }
        papers.append(paper)
    
    return papers

def query_for_pdf(paper_url):
    pdf_url = f"{paper_url}.pdf"
    try:
        with libreq.urlopen(pdf_url) as response:
            return response.read()
    except Exception as e:
        raise Exception(f"Failed to retrieve the PDF: {e}")