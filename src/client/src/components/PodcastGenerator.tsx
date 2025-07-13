import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Download, RefreshCw, Play, Pause } from 'lucide-react';

interface PodcastSettings {
  length: string;
  style: string;
  expertiseLevel: string;
}

interface Document {
  id?: string;
  title?: string;
  name?: string;
  filename?: string;
  url?: string;
}

interface PodcastGeneratorProps {
  settings: PodcastSettings;
  document: Document | null;
  onReset: () => void;
}

const PodcastGenerator: React.FC<PodcastGeneratorProps> = ({ 
  settings, 
  document, 
  onReset 
}) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [podcastUrl, setPodcastUrl] = useState<string>('');
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [audioProgress, setAudioProgress] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  const steps = [
    { id: 'parsing', label: 'Parsing document content', duration: 2000 },
    { id: 'analyzing', label: 'Analyzing key insights', duration: 3000 },
    { id: 'scripting', label: 'Creating podcast script', duration: 4000 },
    { id: 'synthesizing', label: 'Generating audio', duration: 5000 },
    { id: 'finalizing', label: 'Finalizing podcast', duration: 1000 }
  ];

  useEffect(() => {
    if (document) {
      generatePodcast();
    }
  }, [document]);

  const generatePodcast = async () => {
    setIsGenerating(true);
    setProgress(0);
    setCurrentStep('Initializing podcast generation...');

    try {
      // Step 1: Start the podcast generation task
      const requestBody = {
        paper_id: document?.id || '',
        paper_title: document?.title || document?.name || 'Unknown Document',
        settings: {
          length: parseInt(settings.length),
          speakers: settings.style === 'single' ? 1 : 
                   settings.style === 'host-expert' ? 2 :
                   settings.style === 'roundtable-3' ? 3 : 4,
          expertise: settings.expertiseLevel
        }
      };
      
      console.log('Sending podcast generation request:', requestBody);
      
      const response = await fetch('/api/generate_podcast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to start podcast generation');
      }

      const { task_id } = await response.json();
      
      // Step 2: Poll for task completion
      setCurrentStep('Processing document content...');
      setProgress(20);
      
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/task_status/${task_id}`);
          
          if (statusResponse.ok) {
            const result = await statusResponse.json();
            
            if (result.status === 'processing') {
              // Update progress based on current step
              const progressMap = {
                'parsing': 30,
                'analyzing': 50,
                'scripting': 70,
                'synthesizing': 90,
                'finalizing': 95
              };
              
              setProgress(progressMap[result.current_step] || 20);
              setCurrentStep(result.current_step || 'Processing...');
            } else if (result.audio_url) {
              // Task completed successfully
              clearInterval(pollInterval);
              setProgress(100);
              setCurrentStep('Podcast generated successfully!');
              setIsGenerating(false);
              setPodcastUrl(result.audio_url);
              
              // Create audio element for playback
              const audio = new Audio(result.audio_url);
              audio.addEventListener('ended', () => setIsPlaying(false));
              audio.addEventListener('loadedmetadata', () => {
                setAudioDuration(audio.duration);
              });
              audio.addEventListener('timeupdate', () => {
                setCurrentTime(audio.currentTime);
                setAudioProgress((audio.currentTime / audio.duration) * 100);
              });
              setAudioElement(audio);
            } else {
              // Task failed
              clearInterval(pollInterval);
              throw new Error(result.error || 'Podcast generation failed');
            }
          } else {
            throw new Error('Failed to check task status');
          }
        } catch (error) {
          clearInterval(pollInterval);
          console.error('Error polling task status:', error);
          setCurrentStep('Error: Failed to generate podcast');
          setIsGenerating(false);
        }
      }, 2000); // Poll every 2 seconds

    } catch (error) {
      console.error('Error generating podcast:', error);
      setCurrentStep('Error: Failed to start podcast generation');
      setIsGenerating(false);
    }
  };

  const handlePlayPause = () => {
    if (audioElement) {
      if (isPlaying) {
        audioElement.pause();
      } else {
        audioElement.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleDownload = () => {
    if (podcastUrl) {
      // Create a temporary link element to trigger download
      const link = window.document.createElement('a') as HTMLAnchorElement;
      link.href = podcastUrl;
      link.download = `${document?.title || document?.name || 'podcast'}.mp3`;
      window.document.body?.appendChild(link);
      link.click();
      window.document.body?.removeChild(link);
    }
  };

  const getStyleLabel = (style: string) => {
    const styleMap: { [key: string]: string } = {
      'single': 'Single Narrator',
      'host-expert': 'Host & Expert',
      'roundtable-3': 'Roundtable (3 people)',
      'roundtable-4': 'Roundtable (4 people)'
    };
    return styleMap[style] || style;
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Generating Your Podcast</h2>
        <p className="text-gray-600">
          Creating a {settings.length}-minute {getStyleLabel(settings.style).toLowerCase()} 
          podcast for {settings.expertiseLevel} level understanding
        </p>
      </div>

      <Card className="p-8 mb-6">
        {isGenerating ? (
          <div className="space-y-6">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Processing...</h3>
              <p className="text-gray-600">{currentStep}</p>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">What's happening:</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Extracting key concepts and findings</li>
                <li>• Adapting content for your expertise level</li>
                <li>• Creating natural conversation flow</li>
                <li>• Generating high-quality audio</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-6">
            <div className="flex items-center justify-center mb-4">
              <CheckCircle className="h-16 w-16 text-green-500" />
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-green-700 mb-2">
                Podcast Generated Successfully!
              </h3>
              <p className="text-gray-600">
                Your personalized academic podcast is ready to listen
              </p>
            </div>

            {/* Podcast Player Mockup */}
            <Card className="p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-4">
                <div className="flex-1">
                  <h4 className="font-semibold text-left">
                    {document?.title || document?.name || 'Academic Paper Podcast'}
                  </h4>
                  <p className="text-sm text-gray-600 text-left">
                    {Math.round(audioDuration / 60) || settings.length} min • {getStyleLabel(settings.style)}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePlayPause}
                  className="ml-4"
                  disabled={!audioElement}
                >
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${audioProgress}%` }} 
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(audioDuration)}</span>
              </div>
            </Card>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button onClick={handleDownload} className="flex items-center">
                <Download className="h-4 w-4 mr-2" />
                Download Podcast
              </Button>
              
              <Button variant="outline" onClick={onReset} className="flex items-center">
                <RefreshCw className="h-4 w-4 mr-2" />
                Create Another
              </Button>
            </div>

            <div className="text-sm text-gray-600 bg-blue-50 p-4 rounded-lg">
              <p className="font-semibold mb-2">💡 Pro Tips:</p>
              <ul className="text-left space-y-1">
                <li>• Download for offline listening during commutes</li>
                <li>• Adjust playback speed in your audio app</li>
                <li>• Take notes on key insights while listening</li>
              </ul>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default PodcastGenerator;
