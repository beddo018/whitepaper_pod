import requests
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.DEBUG)

def query(query_params):
    url = f'http://export.arxiv.org/api/query?{query_params}'
    response = requests.get(url)
    
    logging.debug(f"Response content: {response.text}")
    
    if response.status_code != 200:
        logging.error(f"Error fetching data from arXiv: {response.status_code}")
        return []
    
    root = ET.fromstring(response.content)
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
        pdf_res = requests.get(pdf_url)
        pdf_res.raise_for_status()
        return pdf_res.content
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to retrieve the PDF: {e}")
