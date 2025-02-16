import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState } from "react";
import HomePage from "./pages/HomePage";
import PromptPage from "./pages/PromptPage";
import PreviewPage from "./pages/PreviewPage";

function App() {
  const [generatedCode, setGeneratedCode] = useState(null);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route 
          path="/prompt" 
          element={<PromptPage setGeneratedCode={setGeneratedCode} />} 
        />
        <Route 
          path="/preview" 
          element={<PreviewPage generatedCode={generatedCode} />} 
        />
      </Routes>
    </Router>
  );
}

export default App;