import { useState } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

const PromptInput = ({ onGenerate }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [characterCount, setCharacterCount] = useState(0);
  const MAX_CHARS = 500;

  const handlePromptChange = (e) => {
    const newValue = e.target.value;
    if (newValue.length <= MAX_CHARS) {
      setPrompt(newValue);
      setCharacterCount(newValue.length);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (prompt.trim().length < 10) {
      setError('Please provide a more detailed description (minimum 10 characters)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/builder/process-prompt/', {
        prompt
      });
      onGenerate(response.data.code);
    } catch (error) {
      setError(error.message || 'Failed to generate website. Please try again.');
      console.error('Generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Website Builder</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <textarea
            value={prompt}
            onChange={handlePromptChange}
            placeholder="Describe your dream website in detail... (e.g., 'Create a modern landing page for a coffee shop with a hero section, menu display, and contact form')"
            disabled={loading}
            className={`w-full min-h-32 p-4 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none
              ${error ? 'border-red-500' : 'border-gray-300'}
              ${loading ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'}
            `}
            aria-label="Website description"
          />
          
          <div className="flex justify-between text-sm">
            <span className={`${characterCount >= MAX_CHARS ? 'text-red-500' : 'text-gray-500'}`}>
              {characterCount}/{MAX_CHARS} characters
            </span>
            {prompt.length < 10 && prompt.length > 0 && (
              <span className="text-red-500 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                Minimum 10 characters required
              </span>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <button 
          type="submit" 
          disabled={loading || prompt.length < 10}
          className={`w-full flex items-center justify-center py-3 px-4 rounded-lg text-white font-medium
            ${loading || prompt.length < 10 
              ? 'bg-blue-300 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:ring-blue-500/50'
            }
          `}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Generating your website...
            </>
          ) : (
            'Build Website'
          )}
        </button>
      </form>
    </div>
  );
};

export default PromptInput;