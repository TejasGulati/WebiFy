import { useState } from 'react';
import { AlertCircle, Loader2, Clock } from 'lucide-react';

const PromptInput = ({ onGenerate }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [characterCount, setCharacterCount] = useState(0);
  const [warnings, setWarnings] = useState([]);
  const [generationTime, setGenerationTime] = useState(null);
  const [debugLog, setDebugLog] = useState([]);

  const MAX_CHARS = 1000;
  const MIN_CHARS = 10;

  const API_ENDPOINTS = {
    process: 'http://127.0.0.1:8000/builder/process-prompt/',
    reset: 'http://127.0.0.1:8000/builder/reset-generation/'
  };

  const addDebugLog = (message, data = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const logMessage = `${timestamp}: ${message}`;
    console.log(logMessage, data);
    setDebugLog(prev => [...prev, { timestamp, message, data }]);
  };

  const handlePromptChange = (e) => {
    const newValue = e.target.value;
    if (newValue.length <= MAX_CHARS) {
      setPrompt(newValue);
      setCharacterCount(newValue.length);
      setError('');
    }
  };

  // Sequential generation steps
  const generateStep = async (currentPrompt) => {
    const response = await fetch(API_ENDPOINTS.process, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: currentPrompt }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Failed to generate step');
    }

    return await response.json();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (prompt.trim().length < MIN_CHARS) {
      const errorMsg = `Please provide a more detailed description (minimum ${MIN_CHARS} characters)`;
      setError(errorMsg);
      addDebugLog(errorMsg);
      return;
    }

    // Reset all states at the start
    setLoading(true);
    setError('');
    setProgress(0);
    setWarnings([]);
    setGenerationTime(null);
    setDebugLog([]);

    const startTime = Date.now();

    try {
      addDebugLog('Starting new generation');

      // Reset any existing generation
      await fetch(API_ENDPOINTS.reset, { method: 'POST' });

      // Structure Analysis (25%)
      addDebugLog('Starting structure analysis');
      setProgress(25);
      const structureResult = await generateStep(prompt);
      if (structureResult.errors?.length) {
        throw new Error(structureResult.errors[0]);
      }

      // HTML Generation (50%)
      addDebugLog('Starting HTML generation');
      setProgress(50);
      const htmlResult = await generateStep(prompt);
      if (htmlResult.errors?.length) {
        throw new Error(htmlResult.errors[0]);
      }

      // CSS Generation (75%)
      addDebugLog('Starting CSS generation');
      setProgress(75);
      const cssResult = await generateStep(prompt);
      if (cssResult.errors?.length) {
        throw new Error(cssResult.errors[0]);
      }

      // JS Generation (100%)
      addDebugLog('Starting JS generation');
      setProgress(100);
      const jsResult = await generateStep(prompt);
      if (jsResult.errors?.length) {
        throw new Error(jsResult.errors[0]);
      }

      // Calculate total generation time
      const endTime = Date.now();
      const totalTime = (endTime - startTime) / 1000; // Convert to seconds
      setGenerationTime(totalTime);

      // Combine all warnings
      const allWarnings = [
        ...(structureResult.warnings || []),
        ...(htmlResult.warnings || []),
        ...(cssResult.warnings || []),
        ...(jsResult.warnings || [])
      ];
      setWarnings(allWarnings);

      // Call onGenerate with final result
      onGenerate(jsResult);
      addDebugLog('Generation completed successfully');

    } catch (err) {
      const errorMsg = err.message || 'Failed to generate website. Please try again.';
      addDebugLog(`Error during generation: ${errorMsg}`);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const getStatusMessage = () => {
    if (!loading) return null;

    const messages = {
      25: 'Analyzing website structure...',
      50: 'Generating HTML markup...',
      75: 'Creating CSS styles...',
      100: 'Adding JavaScript functionality...'
    };

    return messages[progress] || 'Initializing...';
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Website Builder</h1>
        <p className="text-gray-600">
          Describe your website and we'll generate it using AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <textarea
            value={prompt}
            onChange={handlePromptChange}
            placeholder="Describe your website in detail..."
            className="w-full h-32 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          />

          <div className="flex justify-between text-sm">
            <span className={characterCount >= MAX_CHARS ? 'text-red-500' : 'text-gray-500'}>
              {characterCount}/{MAX_CHARS} characters
            </span>
            {prompt.length < MIN_CHARS && prompt.length > 0 && (
              <span className="text-red-500 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                Minimum {MIN_CHARS} characters required
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

        {warnings.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
            <div className="text-yellow-800">
              {warnings.map((warning, index) => (
                <div key={index}>{warning}</div>
              ))}
            </div>
          </div>
        )}

        {loading && progress > 0 && (
          <div className="space-y-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {getStatusMessage()}
              </span>
              <span>{progress}%</span>
            </div>
          </div>
        )}

        {generationTime && !loading && (
          <div className="text-sm text-gray-600">
            Generation completed in {generationTime.toFixed(2)} seconds
          </div>
        )}

        <button
          type="submit"
          disabled={loading || prompt.length < MIN_CHARS}
          className={`w-full flex items-center justify-center py-3 px-4 rounded-lg text-white font-medium
            ${loading || prompt.length < MIN_CHARS
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