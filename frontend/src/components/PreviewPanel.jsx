import React, { useEffect, useState } from 'react';
import { AlertCircle, Loader2, Code, Maximize2, RefreshCw } from 'lucide-react';

const PreviewPanel = ({ code, loading, error }) => {
  const [previewKey, setPreviewKey] = useState(0);
  const [showCode, setShowCode] = useState(false);

  // Update image paths to use the full backend URL
  const updateImagePaths = (htmlContent) => {
    if (!htmlContent) return htmlContent;
    
    const BACKEND_URL = 'http://localhost:8000/';
    const updatedHTML = htmlContent.replace(
      /<img([^>]*)src=["'](?:\/?images\/[^"']*)["']([^>]*)>/g,
      (match, before, after) => {
        const srcMatch = match.match(/src=["']([^"']*)["']/);
        if (srcMatch) {
          const originalSrc = srcMatch[1];
          const cleanPath = originalSrc.replace(/^\/+/, '');
          return `<img${before}src="${BACKEND_URL}${cleanPath}"${after}>`;
        }
        return match;
      }
    );
    
    return updatedHTML;
  };

  const generatePreviewCode = (code) => {
    if (!code?.html && !code?.css && !code?.js) return null;

    const updatedHTML = updateImagePaths(code?.html || '');

    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>${code?.css || ''}</style>
        </head>
        <body>
          ${updatedHTML}
          <script>${code?.js || ''}</script>
        </body>
      </html>
    `;
  };

  useEffect(() => {
    setPreviewKey(prev => prev + 1);
  }, [code]);

  if (error) {
    return (
      <div className="error-container">
        <AlertCircle className="icon" />
        <span>{error}</span>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-content">
          <Loader2 className="icon spinning" />
          <p>Generating your website preview...</p>
        </div>
      </div>
    );
  }

  const previewCode = generatePreviewCode(code);

  if (!previewCode) {
    return (
      <div className="empty-container">
        <div className="empty-content">
          <div className="icon-container">
            <Code className="icon" />
          </div>
          <div className="empty-text">
            <p className="empty-title">Preview Panel</p>
            <p className="empty-description">Your generated website will appear here</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="preview-container">
      <div className="preview-header">
        <h2 className="preview-title">Website Preview</h2>
        <div className="preview-actions">
          <button
            onClick={() => setShowCode(!showCode)}
            className="action-button"
          >
            <Code className="icon" />
            {showCode ? 'Hide Code' : 'Show Code'}
          </button>
          <button
            onClick={() => setPreviewKey(prev => prev + 1)}
            className="action-button"
          >
            <RefreshCw className="icon" />
            Refresh
          </button>
          <button
            onClick={() => {
              const newWindow = window.open('', '_blank');
              newWindow.document.write(previewCode);
              newWindow.document.close();
            }}
            className="action-button"
          >
            <Maximize2 className="icon" />
            Open in New Tab
          </button>
        </div>
      </div>

      {showCode && (
        <pre className="code-preview">
          <code>{previewCode}</code>
        </pre>
      )}

      <div className="iframe-container">
        <iframe
          key={previewKey}
          srcDoc={previewCode}
          title="Website Preview"
          className="preview-iframe"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
};

export default PreviewPanel;