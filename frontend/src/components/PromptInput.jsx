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

  // Sequential generation steps remain unchanged
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

    setLoading(true);
    setError('');
    setProgress(0);
    setWarnings([]);
    setGenerationTime(null);
    setDebugLog([]);

    const startTime = Date.now();

    try {
      addDebugLog('Starting new generation');
      await fetch(API_ENDPOINTS.reset, { method: 'POST' });

      addDebugLog('Starting structure analysis');
      setProgress(25);
      const structureResult = await generateStep(prompt);
      if (structureResult.errors?.length) {
        throw new Error(structureResult.errors[0]);
      }

      addDebugLog('Starting HTML generation');
      setProgress(50);
      const htmlResult = await generateStep(prompt);
      if (htmlResult.errors?.length) {
        throw new Error(htmlResult.errors[0]);
      }

      addDebugLog('Starting CSS generation');
      setProgress(75);
      const cssResult = await generateStep(prompt);
      if (cssResult.errors?.length) {
        throw new Error(cssResult.errors[0]);
      }

      addDebugLog('Starting JS generation');
      setProgress(100);
      const jsResult = await generateStep(prompt);
      if (jsResult.errors?.length) {
        throw new Error(jsResult.errors[0]);
      }

      const endTime = Date.now();
      const totalTime = (endTime - startTime) / 1000;
      setGenerationTime(totalTime);

      const allWarnings = [
        ...(structureResult.warnings || []),
        ...(htmlResult.warnings || []),
        ...(cssResult.warnings || []),
        ...(jsResult.warnings || [])
      ];
      setWarnings(allWarnings);

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
    <div className="input-container">
      <div className="input-header">
        <h1 className="title">Website Builder</h1>
        <p className="subtitle">
          Describe your website and we'll generate it using AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="textarea-container">
          <textarea
            value={prompt}
            onChange={handlePromptChange}
            placeholder="Describe your website in detail..."
            className="prompt-textarea"
            disabled={loading}
          />

          <div className="character-count">
            <span className={characterCount >= MAX_CHARS ? 'error' : ''}>
              {characterCount}/{MAX_CHARS} characters
            </span>
            {prompt.length < MIN_CHARS && prompt.length > 0 && (
              <span className="min-chars-warning">
                <AlertCircle className="icon" />
                Minimum {MIN_CHARS} characters required
              </span>
            )}
          </div>
        </div>

        {error && (
          <div className="error-message">
            <AlertCircle className="icon" />
            <p>{error}</p>
          </div>
        )}

        {warnings.length > 0 && (
          <div className="warning-message">
            <AlertCircle className="icon" />
            <div className="warning-content">
              {warnings.map((warning, index) => (
                <div key={index}>{warning}</div>
              ))}
            </div>
          </div>
        )}

        {loading && progress > 0 && (
          <div className="progress-container">
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="progress-status">
              <span className="status-message">
                <Clock className="icon" />
                {getStatusMessage()}
              </span>
              <span className="progress-percentage">{progress}%</span>
            </div>
          </div>
        )}

        {generationTime && !loading && (
          <div className="generation-time">
            Generation completed in {generationTime.toFixed(2)} seconds
          </div>
        )}

        <button
          type="submit"
          disabled={loading || prompt.length < MIN_CHARS}
          className={`submit-button ${loading || prompt.length < MIN_CHARS ? 'disabled' : ''}`}
        >
          {loading ? (
            <>
              <Loader2 className="icon spinning" />
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