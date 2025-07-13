
import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Search, Upload, Headphones } from 'lucide-react';
import PaperSearch from '@/components/PaperSearch';
import PdfUpload from '@/components/PdfUpload';
import PodcastCustomizer from '@/components/PodcastCustomizer';
import PodcastGenerator from '@/components/PodcastGenerator';

type Step = 'select' | 'search' | 'upload' | 'customize' | 'generate';
type PodcastSettings = {
  length: string;
  style: string;
  expertiseLevel: string;
};

const Index = () => {
  const [currentStep, setCurrentStep] = useState<Step>('select');
  const [selectedPaper, setSelectedPaper] = useState<any>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [podcastSettings, setPodcastSettings] = useState<PodcastSettings>({
    length: '',
    style: '',
    expertiseLevel: ''
  });

  const handlePaperSelect = (paper: any) => {
    setSelectedPaper(paper);
    setCurrentStep('customize');
  };

  const handleFileUpload = (file: File) => {
    setUploadedFile(file);
    setCurrentStep('customize');
  };

  const handleCustomizationComplete = (settings: PodcastSettings) => {
    setPodcastSettings(settings);
    setCurrentStep('generate');
  };

  const resetToStart = () => {
    setCurrentStep('select');
    setSelectedPaper(null);
    setUploadedFile(null);
    setPodcastSettings({ length: '', style: '', expertiseLevel: '' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Headphones className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              ParsePod
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Transform academic papers into personalized podcasts for your commute. 
            Stay current with research in your field, anywhere, anytime.
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`w-3 h-3 rounded-full ${currentStep === 'select' ? 'bg-blue-600' : ['search', 'upload', 'customize', 'generate'].includes(currentStep) ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className={`w-12 h-1 ${currentStep === 'search' || currentStep === 'upload' ? 'bg-blue-600' : (currentStep === 'customize' || currentStep === 'generate') ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className={`w-3 h-3 rounded-full ${currentStep === 'search' || currentStep === 'upload' ? 'bg-blue-600' : (currentStep === 'customize' || currentStep === 'generate') ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className={`w-12 h-1 ${currentStep === 'customize' ? 'bg-blue-600' : currentStep === 'generate' ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className={`w-3 h-3 rounded-full ${currentStep === 'customize' ? 'bg-blue-600' : currentStep === 'generate' ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className={`w-12 h-1 ${currentStep === 'generate' ? 'bg-blue-600' : 'bg-gray-300'}`} />
            <div className={`w-3 h-3 rounded-full ${currentStep === 'generate' ? 'bg-blue-600' : 'bg-gray-300'}`} />
          </div>
        </div>

        {/* Main Content */}
        <div className="w-full">
          {currentStep === 'select' && (
            <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-blue-200" 
                    onClick={() => setCurrentStep('search')}>
                <div className="text-center">
                  <Search className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Search Papers</h3>
                  <p className="text-gray-600">
                    Find and select academic papers using keyword search
                  </p>
                </div>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-blue-200" 
                    onClick={() => setCurrentStep('upload')}>
                <div className="text-center">
                  <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Upload PDF</h3>
                  <p className="text-gray-600">
                    Upload your own PDF document to convert
                  </p>
                </div>
              </Card>
            </div>
          )}

          {currentStep === 'search' && (
            <PaperSearch 
              onPaperSelect={handlePaperSelect}
              onBack={() => setCurrentStep('select')}
            />
          )}

          {currentStep === 'upload' && (
            <PdfUpload 
              onFileUpload={handleFileUpload}
              onBack={() => setCurrentStep('select')}
            />
          )}

          {currentStep === 'customize' && (
            <PodcastCustomizer 
              onComplete={handleCustomizationComplete}
              onBack={() => setCurrentStep(selectedPaper ? 'search' : 'upload')}
              documentTitle={selectedPaper?.title || uploadedFile?.name || ''}
            />
          )}

          {currentStep === 'generate' && (
            <PodcastGenerator 
              settings={podcastSettings}
              document={selectedPaper || uploadedFile}
              onReset={resetToStart}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
