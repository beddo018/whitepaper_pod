import unittest
import os
import io
from unittest.mock import patch, MagicMock
from app import app
from pdf_processor import process_pdf, extract_text_from_pdf, extract_images_from_pdf
from server.generate_transcript.transcript_generator import generate_transcript
from text_to_speech_local import convert_to_audio
from arxiv import query, query_for_pdf

class WhitepaperPodTest(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        # Create test directories if they don't exist
        os.makedirs('static/audio', exist_ok=True)
        os.makedirs('tmp', exist_ok=True)
    
    @patch('arxiv.requests.get')
    def test_arxiv_query(self, mock_get):
        # Mock the response from arXiv API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/1234.5678</id>
            <title>Test Paper</title>
            <summary>This is a test summary</summary>
            <published>2023-01-01T00:00:00Z</published>
            <author>
              <name>Test Author</name>
            </author>
            <link href="http://arxiv.org/abs/1234.5678" rel="alternate" type="text/html"/>
            <link href="http://arxiv.org/pdf/1234.5678" rel="related" type="application/pdf"/>
          </entry>
        </feed>'''
        mock_get.return_value = mock_response
        
        # Test the query function
        papers = query("search_query=test&max_results=1")
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['title'], 'Test Paper')
        self.assertEqual(papers[0]['authors'], ['Test Author'])
    
    @patch('arxiv.requests.get')
    def test_arxiv_query_for_pdf(self, mock_get):
        # Mock the response for PDF request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Mock PDF content'
        mock_get.return_value = mock_response
        
        # Test the query_for_pdf function
        pdf_content = query_for_pdf('http://arxiv.org/abs/1234.5678')
        self.assertEqual(pdf_content, b'Mock PDF content')
    
    @patch('pdfplumber.open')
    def test_extract_text_from_pdf(self, mock_pdf_open):
        # Mock PDF processing
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content page 1"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf_open.return_value = mock_pdf
        
        # Test text extraction
        text = extract_text_from_pdf(b'Mock PDF content')
        self.assertEqual(text, "Test content page 1\n")
    
    @patch('transcript_generator.client')
    @patch('os.getenv')
    def test_generate_transcript(self, mock_getenv, mock_client):
        # Mock the API key
        mock_getenv.return_value = "test_api_key"
        
        # Create mock response that matches the new SDK format
        mock_message = MagicMock()
        mock_message.text = "<speak>Generated transcript</speak>"  # Changed from content to text
        mock_response = MagicMock()
        mock_response.content = [mock_message]
        mock_client.messages.create.return_value = mock_response

        # Test transcript generation
        paper = {
            'title': 'Test Paper',
            'summary': 'This is a test summary'
        }
        transcript = generate_transcript(paper)
        self.assertEqual(transcript, "<speak>Generated transcript</speak>")
        
        # Verify the API was called with correct parameters
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args['model'], "claude-3-sonnet-20240229")
        self.assertEqual(call_args['max_tokens'], 1500)
        self.assertEqual(call_args['temperature'], 0.7)
    
    @patch('TTS.api.TTS')
    @patch('sqlite3.connect')
    def test_convert_to_audio(self, mock_db_connect, mock_tts):
        # Mock TTS and database
        mock_tts_instance = MagicMock()
        mock_tts.return_value = mock_tts_instance
        
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db_connect.return_value = mock_connection
        
        # Create a temporary audio file for testing
        test_audio_path = 'static/audio/test_audio.mp3'
        with open(test_audio_path, 'wb') as f:
            f.write(b'test audio content')
        
        # Mock the TTS file creation
        def side_effect(text, file_path):
            with open(file_path, 'wb') as f:
                f.write(b'test audio content')
        
        mock_tts_instance.tts_to_file.side_effect = side_effect
        
        # Test audio conversion
        result = convert_to_audio("<speak>Test transcript</speak>", "test_audio.mp3")
        self.assertEqual(result, 'static/audio/test_audio.mp3')
        
        # Clean up
        os.remove(test_audio_path)
    
    def test_app_index_route(self):
        # Test the main route
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.query')
    def test_app_search_papers(self, mock_query):
        # Mock arXiv query
        mock_query.return_value = [
            {
                'id': 'http://arxiv.org/abs/1234.5678',
                'title': 'Test Paper',
                'summary': 'This is a test summary',
                'published': '2023-01-01T00:00:00Z',
                'authors': ['Test Author'],
                'pdf_url': 'http://arxiv.org/pdf/1234.5678'
            }
        ]
        
        # Test search_papers route
        response = self.client.post('/search_papers', 
                                   json={'query_string': 'test'})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Paper')
    
    @patch('app.process_paper_async')
    def test_generate_podcast(self, mock_process):
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = 'test_task_id'
        mock_process.delay.return_value = mock_task
        
        # Test generate_podcast route
        response = self.client.post('/generate_podcast', 
                                   json={
                                       'paper_id': 'http://arxiv.org/abs/1234.5678',
                                       'paper_title': 'Test Paper'
                                   })
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['task_id'], 'test_task_id')

if __name__ == '__main__':
    unittest.main()