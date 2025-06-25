
import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Upload, FileText, X } from 'lucide-react';

interface PdfUploadProps {
  onFileUpload: (file: File) => void;
  onBack: () => void;
}

const PdfUpload: React.FC<PdfUploadProps> = ({ onFileUpload, onBack }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');

  const validateFile = useCallback((file: File): string | null => {
    if (file.type !== 'application/pdf') {
      return 'Please select a PDF file.';
    }
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      return 'File size must be less than 10MB.';
    }
    return null;
  }, []);

  const handleFile = useCallback((file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError('');
    setSelectedFile(file);
  }, [validateFile]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0]);
    }
  }, [handleFile]);

  const removeFile = () => {
    setSelectedFile(null);
    setError('');
  };

const handleUpload = async () => {
  if (selectedFile) {
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/upload_pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload PDF');
      }

      const data = await response.json();
      onFileUpload(data); // Pass the response data to the parent component
    } catch (error) {
      console.error('Error uploading PDF:', error);
      setError('Failed to upload PDF. Please try again.');
    }
  }
};

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center mb-6">
        <Button variant="outline" onClick={onBack} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h2 className="text-2xl font-bold">Upload PDF Document</h2>
      </div>

      <Card className="p-8">
        {!selectedFile ? (
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">
              Drop your PDF here, or click to browse
            </h3>
            <p className="text-gray-600 mb-6">
              Upload academic papers, research documents, or technical reports
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Maximum file size: 10MB • Supported format: PDF
            </p>
            
            <Button asChild>
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileInput}
                  className="hidden"
                />
                Choose File
              </label>
            </Button>
            
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <FileText className="h-8 w-8 text-green-600 mr-3" />
                <div>
                  <h4 className="font-semibold text-green-900">{selectedFile.name}</h4>
                  <p className="text-sm text-green-700">
                    {formatFileSize(selectedFile.size)} • PDF Document
                  </p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={removeFile}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="text-center">
              <p className="text-gray-600 mb-4">
                Ready to convert this document to a podcast?
              </p>
              <Button onClick={handleUpload} className="px-8">
                Continue to Customization
              </Button>
            </div>
          </div>
        )}
      </Card>

      <div className="mt-6 text-center">
        <h3 className="text-lg font-semibold mb-3">Supported Documents</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div>
            <strong>Research Papers</strong>
            <br />
            Peer-reviewed articles, conference papers
          </div>
          <div>
            <strong>Technical Reports</strong>
            <br />
            Whitepapers, technical documentation
          </div>
          <div>
            <strong>Academic Content</strong>
            <br />
            Thesis chapters, review articles
          </div>
        </div>
      </div>
    </div>
  );
};

export default PdfUpload;
