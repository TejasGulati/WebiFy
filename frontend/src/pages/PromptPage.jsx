import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Code, Send, Sparkles } from "lucide-react";
import PromptInput from "../components/PromptInput";
import { useNavigate } from "react-router-dom";

function PromptPage({ setGeneratedCode }) {
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

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
            <li><Link to="/preview" className="nav-link">Preview</Link></li>
          </ul>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-content">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="hero-title"
          >
            Let AI Build Your Website
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hero-subtitle"
          >
            Describe your vision and watch as AI transforms it into beautiful, responsive code.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="prompt-container"
          >
            <div className="feature-card prompt-card">
              <div className="feature-icon">
                <Sparkles className="w-8 h-8" />
              </div>
              <PromptInput 
                onGenerate={(code) => {
                  setGeneratedCode(code);
                  navigate('/preview');
                }}
              />
            </div>
          </motion.div>

          <section className="features" style={{ paddingTop: '2rem' }}>
            <div className="feature-grid">
              <motion.div 
                className="feature-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <div className="feature-icon">
                  <Send className="w-8 h-8" />
                </div>
                <h3>Be Descriptive</h3>
                <p>The more details you provide about your desired website, the better the results will be.</p>
              </motion.div>

              <motion.div 
                className="feature-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <div className="feature-icon">
                  <Code className="w-8 h-8" />
                </div>
                <h3>Specify Features</h3>
                <p>Mention specific features, layouts, or components you want in your website.</p>
              </motion.div>
            </div>
          </section>
        </div>
      </header>

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

export default PromptPage;