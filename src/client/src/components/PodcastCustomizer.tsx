
import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Clock, Users, GraduationCap } from 'lucide-react';

interface PodcastSettings {
  length: string;
  style: string;
  expertiseLevel: string;
}

interface PodcastCustomizerProps {
  onComplete: (settings: PodcastSettings) => void;
  onBack: () => void;
  documentTitle: string;
}

const PodcastCustomizer: React.FC<PodcastCustomizerProps> = ({ 
  onComplete, 
  onBack, 
  documentTitle 
}) => {
  const [settings, setSettings] = useState<PodcastSettings>({
    length: '',
    style: '',
    expertiseLevel: ''
  });

  const lengthOptions = [
    { value: '5', label: '5 minutes', description: 'Quick overview of key points' },
    { value: '10', label: '10 minutes', description: 'Balanced summary with main insights' },
    { value: '15', label: '15 minutes', description: 'Detailed discussion of findings' },
    { value: '20', label: '20 minutes', description: 'Comprehensive analysis' }
  ];

  const styleOptions = [
    { 
      value: 'single', 
      label: 'Single Narrator', 
      description: 'One expert presenter explaining the content',
      participants: 1 
    },
    { 
      value: 'host-expert', 
      label: 'Host & Expert', 
      description: 'Interview-style conversation',
      participants: 2 
    },
    { 
      value: 'roundtable-3', 
      label: 'Roundtable (3 people)', 
      description: 'Panel discussion with multiple perspectives',
      participants: 3 
    },
    { 
      value: 'roundtable-4', 
      label: 'Roundtable (4 people)', 
      description: 'Extended panel with diverse viewpoints',
      participants: 4 
    }
  ];

  const expertiseOptions = [
    { 
      value: 'beginner', 
      label: 'Beginner', 
      description: 'New to the field, need fundamental concepts explained' 
    },
    { 
      value: 'intermediate', 
      label: 'Intermediate', 
      description: 'Some background knowledge, comfortable with technical terms' 
    },
    { 
      value: 'advanced', 
      label: 'Advanced', 
      description: 'Strong background, focus on novel insights and implications' 
    },
    { 
      value: 'expert', 
      label: 'Expert', 
      description: 'Deep domain knowledge, interested in nuanced analysis' 
    }
  ];

  const handleSettingChange = (key: keyof PodcastSettings, value: string) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const isComplete = settings.length && settings.style && settings.expertiseLevel;

  const handleGenerate = () => {
    if (isComplete) {
      onComplete(settings);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center mb-6">
        <Button variant="outline" onClick={onBack} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h2 className="text-2xl font-bold">Customize Your Podcast</h2>
      </div>

      <Card className="p-6 mb-6">
        <div className="flex items-center mb-4">
          <div className="h-2 w-2 bg-green-500 rounded-full mr-3" />
          <span className="font-medium">Document Selected:</span>
        </div>
        <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
          {documentTitle}
        </p>
      </Card>

      <div className="space-y-8">
        {/* Podcast Length */}
        <Card className="p-6">
          <div className="flex items-center mb-4">
            <Clock className="h-5 w-5 text-blue-600 mr-2" />
            <Label className="text-lg font-semibold">Podcast Length</Label>
          </div>
          <Select onValueChange={(value) => handleSettingChange('length', value)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Choose podcast duration" />
            </SelectTrigger>
            <SelectContent>
              {lengthOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="py-2">
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-600">{option.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Card>

        {/* Podcast Style */}
        <Card className="p-6">
          <div className="flex items-center mb-4">
            <Users className="h-5 w-5 text-blue-600 mr-2" />
            <Label className="text-lg font-semibold">Podcast Style</Label>
          </div>
          <Select onValueChange={(value) => handleSettingChange('style', value)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Choose presentation style" />
            </SelectTrigger>
            <SelectContent>
              {styleOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="py-2">
                    <div className="font-medium flex items-center">
                      {option.label}
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        {option.participants} {option.participants === 1 ? 'person' : 'people'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">{option.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Card>

        {/* Expertise Level */}
        <Card className="p-6">
          <div className="flex items-center mb-4">
            <GraduationCap className="h-5 w-5 text-blue-600 mr-2" />
            <Label className="text-lg font-semibold">Your Expertise Level</Label>
          </div>
          <Select onValueChange={(value) => handleSettingChange('expertiseLevel', value)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select your background in this field" />
            </SelectTrigger>
            <SelectContent>
              {expertiseOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="py-2">
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-gray-600">{option.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Card>

        {/* Generate Button */}
        <div className="text-center pt-4">
          <Button 
            onClick={handleGenerate}
            disabled={!isComplete}
            size="lg"
            className="px-12 py-3 text-lg"
          >
            {isComplete ? 'Generate Podcast' : 'Complete All Settings'}
          </Button>
          
          {isComplete && (
            <p className="text-sm text-gray-600 mt-3">
              This will create a {settings.length}-minute {styleOptions.find(s => s.value === settings.style)?.label.toLowerCase()} 
              podcast tailored for {settings.expertiseLevel} level understanding.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PodcastCustomizer;
