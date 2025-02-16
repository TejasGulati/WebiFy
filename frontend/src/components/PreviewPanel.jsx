import React, { useEffect, useState } from 'react';
import { AlertCircle, Loader2, Code, Maximize2, RefreshCw } from 'lucide-react';

const PreviewPanel = ({ code, loading, error }) => {
  const [previewKey, setPreviewKey] = useState(0);
  const [showCode, setShowCode] = useState(false);

  // Update image paths to use the full backend URL
  const updateImagePaths = (htmlContent) => {
    if (!htmlContent) return htmlContent;
    
    // Replace image paths with absolute URLs
    // Match any img tag with src containing "images/"
    const BACKEND_URL = 'http://localhost:8000/'; // Make sure this matches your Django development server
    const updatedHTML = htmlContent.replace(
      /<img([^>]*)src=["'](?:\/?images\/[^"']*)["']([^>]*)>/g,
      (match, before, after) => {
        // Extract the original src
        const srcMatch = match.match(/src=["']([^"']*)["']/);
        if (srcMatch) {
          const originalSrc = srcMatch[1];
          // Clean up the path and create absolute URL
          const cleanPath = originalSrc.replace(/^\/+/, ''); // Remove leading slashes
          return `<img${before}src="${BACKEND_URL}${cleanPath}"${after}>`;
        }
        return match;
      }
    );
    
    return updatedHTML;
  };

  // Combine HTML, CSS, and JS into a single document
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

  // Force iframe refresh when code changes
  useEffect(() => {
    setPreviewKey(prev => prev + 1);
  }, [code]);

  if (error) {
    return (
      <div className="mb-4 p-4 border border-red-500 bg-red-100 rounded-lg flex items-center">
        <AlertCircle className="h-4 w-4 text-red-500 mr-2" />
        <span>{error}</span>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg border">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
          <p className="text-gray-600">Generating your website preview...</p>
        </div>
      </div>
    );
  }

  const previewCode = generatePreviewCode(code);

  if (!previewCode) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg border">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto">
            <Code className="h-8 w-8 text-blue-500" />
          </div>
          <div>
            <p className="text-lg font-medium">Preview Panel</p>
            <p className="text-gray-600">Your generated website will appear here</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Website Preview</h2>
        <div className="space-x-2">
          <button
            onClick={() => setShowCode(!showCode)}
            className="inline-flex items-center px-3 py-1.5 border rounded-md hover:bg-gray-50"
          >
            <Code className="h-4 w-4 mr-2" />
            {showCode ? 'Hide Code' : 'Show Code'}
          </button>
          <button
            onClick={() => setPreviewKey(prev => prev + 1)}
            className="inline-flex items-center px-3 py-1.5 border rounded-md hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => {
              const newWindow = window.open('', '_blank');
              newWindow.document.write(previewCode);
              newWindow.document.close();
            }}
            className="inline-flex items-center px-3 py-1.5 border rounded-md hover:bg-gray-50"
          >
            <Maximize2 className="h-4 w-4 mr-2" />
            Open in New Tab
          </button>
        </div>
      </div>

      {showCode && (
        <pre className="p-4 bg-gray-50 rounded-lg overflow-auto max-h-96">
          <code>{previewCode}</code>
        </pre>
      )}

      <div className="border rounded-lg overflow-hidden bg-white">
        <iframe
          key={previewKey}
          srcDoc={previewCode}
          title="Website Preview"
          className="w-full h-[600px] border-0"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
};

export default PreviewPanel;
