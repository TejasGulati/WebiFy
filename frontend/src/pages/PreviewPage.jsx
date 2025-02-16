import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MonitorPlay, ArrowLeft, Code, Share } from "lucide-react";
import PreviewPanel from "../components/PreviewPanel";
import { useNavigate } from "react-router-dom";

function PreviewPage({ generatedCode }) {
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    if (!generatedCode) {
      navigate('/prompt');
    }
  }, [generatedCode, navigate]);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="app">
      <nav className={`navbar ${isScrolled ? "navbar-scrolled" : ""}`}>
        <div className="navbar-content">
          <h2 className="logo">
            <span className="logo-text">Webify</span>
            <span className="logo-dot">.</span>
          </h2>
          <ul className="nav-links">
            <li><Link to="/" className="nav-link">Home</Link></li>
            <li><Link to="/prompt" className="nav-link">Prompt Input</Link></li>
          </ul>
        </div>
      </nav>

      <header className="hero" style={{ minHeight: 'auto', paddingBottom: '2rem' }}>
        <div className="hero-content">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="hero-title"
          >
            Preview Your Website
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hero-subtitle"
          >
            See your AI-generated website come to life in real-time.
          </motion.p>
        </div>
      </header>

      <main className="preview-main">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="container"
          style={{ padding: '2rem var(--container-padding)' }}
        >
          <div className="feature-card preview-container" style={{ padding: '0', overflow: 'hidden' }}>
            <div className="preview-header" style={{ 
              padding: '1rem 1.5rem',
              borderBottom: '1px solid var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <MonitorPlay className="w-5 h-5" style={{ 
                background: 'var(--feature-gradient-1)',
                WebkitBackgroundClip: 'text',
                backgroundClip: 'text',
                color: 'transparent'
              }}/>
              <span style={{ fontWeight: '600' }}>Live Preview</span>
            </div>
            <div className="preview-content" style={{ padding: '1.5rem' }}>
              <PreviewPanel code={generatedCode} />
            </div>
          </div>

          <motion.div 
            className="feature-grid"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            style={{ marginTop: '2rem' }}
          >
            <div className="feature-card">
              <div className="feature-icon">
                <Code className="w-8 h-8" />
              </div>
              <h3>View Source Code</h3>
              <p>Examine the generated code and make custom modifications if needed.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <Share className="w-8 h-8" />
              </div>
              <h3>Export Project</h3>
              <p>Download your project files or share them directly with your team.</p>
            </div>
          </motion.div>
        </motion.div>
      </main>

      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>Webify</h3>
            <p>Making web development smarter, faster, and more accessible.</p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2025 Webify. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default PreviewPage;