import { useState } from 'react';
import axios from 'axios';

const PromptInput = ({ onGenerate }) => {
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await axios.post('http://localhost:8000/builder/process-prompt/', {
                prompt
            });
            onGenerate(response.data.code);
        } catch (error) {
            console.error('Generation failed:', error);
        }
        setLoading(false);
    };

    return (
        <form onSubmit={handleSubmit}>
            <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your website..."
                disabled={loading}
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Generating...' : 'Build Website'}
            </button>
        </form>
    );
};

export default PromptInput;
