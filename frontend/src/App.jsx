import { useState } from 'react';
import PromptInput from './components/PromptInput';
import PreviewPanel from './components/PreviewPanel';

function App() {
    const [generatedCode, setGeneratedCode] = useState('');

    return (
        <div className="app">
            <h1>Webify - AI Website Builder</h1>
            <PromptInput onGenerate={setGeneratedCode} />
            <PreviewPanel code={generatedCode} />
        </div>
    );
}

export default App;
