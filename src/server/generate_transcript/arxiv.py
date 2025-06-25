import urllib.request as libreq
import urllib.parse as libparse
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.DEBUG)

def query(query_params):
    # Encode the query_params string to handle spaces and special characters
    encoded_params = libparse.quote(query_params, safe='=&')
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
    pdf_url = paper_url.replace('abs','pdf')
    print(pdf_url)
    try:
        with libreq.urlopen(pdf_url) as response:
            print(response.headers)
            return response.read().decode(response.headers.get_content_charset())
    except Exception as e:
        raise Exception(f"Failed to retrieve the PDF: {e}")
    
if __name__ == "__main__":
    content = query_for_pdf("http://arxiv.org/abs/1911.06612v1")
    print("ARTICLE SUMMARY:\n~~~~~~~~\n")

    print(f"String saved to {file_name}")
    
    print("ARTICLE END:\n~~~~~~~~\n")