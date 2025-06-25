import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, ArrowLeft, ExternalLink } from 'lucide-react';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publishedDate: string;
  journal: string;
  url: string;
}

interface PaperSearchProps {
  onPaperSelect: (paper: Paper) => void;
  onBack: () => void;
}

const PaperSearch: React.FC<PaperSearchProps> = ({ onPaperSelect, onBack }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Paper[]>([]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);

    try {
      const response = await fetch('/api/search_papers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_string: searchQuery }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch papers');
      }

      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Error fetching papers:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center mb-6">
        <Button variant="outline" onClick={onBack} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h2 className="text-2xl font-bold">Search Academic Papers</h2>
      </div>

      <Card className="p-6 mb-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Search for papers (e.g., 'machine learning', 'climate change', 'cancer research')"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full"
            />
          </div>
          <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
            <Search className="h-4 w-4 mr-2" />
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </Card>

      {searchResults.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Search Results</h3>
          {searchResults.map((paper) => (
            <Card key={paper.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="text-lg font-semibold mb-2">{paper.title}</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    {paper.authors.join(', ')} • {paper.journal} • {paper.publishedDate}
                  </p>
                  <p className="text-gray-700 mb-4 line-clamp-3">{paper.abstract}</p>
                  <div className="flex gap-2">
                    <Button onClick={() => onPaperSelect(paper)}>
                      Select Paper
                    </Button>
                    <Button variant="outline" asChild>
                      <a href={paper.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View Paper
                      </a>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {searchResults.length === 0 && searchQuery && !isSearching && (
        <Card className="p-6 text-center">
          <p className="text-gray-600">No papers found for your search query.</p>
          <p className="text-sm text-gray-500 mt-2">Try different keywords or check your spelling.</p>
        </Card>
      )}
    </div>
  );
};

export default PaperSearch;