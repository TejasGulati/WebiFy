const PreviewPanel = ({ code }) => {
    return (
        <div className="preview-container">
            {code ? (
                <iframe 
                    srcDoc={code}
                    title="preview"
                    style={{ width: '100%', height: '500px', border: 'none' }}
                />
            ) : (
                <p>Your generated website will appear here...</p>
            )}
        </div>
    );
};

export default PreviewPanel;
