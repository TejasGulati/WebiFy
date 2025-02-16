import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Code, Smartphone, Palette } from "lucide-react";

function HomePage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const features = [
    {
      icon: <Code className="w-8 h-8" />,
      title: "AI-Powered Development",
      description: "Generate production-ready code with our advanced AI engine. Support for React, Vue, and Angular frameworks."
    },
    {
      icon: <Smartphone className="w-8 h-8" />,
      title: "Responsive Design System",
      description: "Automatically optimized for all devices with our intelligent responsive grid system and flexible components."
    },
    {
      icon: <Palette className="w-8 h-8" />,
      title: "Advanced Customization",
      description: "Fine-tune every aspect of your website with our powerful theme engine and real-time preview."
    }
  ];

  return (
    <div className="app">
      {/* Simplified Navbar */}
      <nav className={`navbar ${isScrolled ? "navbar-scrolled" : ""}`}>
        <div className="navbar-content">
          <h2 className="logo">
            <span className="logo-text">Webify</span>
            <span className="logo-dot">.</span>
          </h2>
          <ul className="nav-links">
            <li><Link to="/prompt" className="nav-link">Get Started</Link></li>
            <li><Link to="/preview" className="nav-link">Preview</Link></li>
          </ul>
        </div>
      </nav>

      {/* Enhanced Hero Section */}
      <header className="hero">
        <div className="hero-content">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="hero-title"
          >
            Transform Your Ideas Into Reality with AI
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hero-subtitle"
          >
            Create stunning, responsive websites in minutes with our AI-powered platform.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="hero-cta"
          >
            <Link to="/prompt" className="btn btn-primary">
              Start Building <ArrowRight className="btn-icon" />
            </Link>
          </motion.div>
        </div>
        <div className="hero-shape"></div>
      </header>

      {/* Enhanced Features Section */}
      <section className="features">
        <h2 className="section-title">Powerful Features</h2>
        <div className="feature-grid">
          {features.map((feature, index) => (
            <motion.div 
              key={index}
              className={`feature-card ${activeFeature === index ? 'active' : ''}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.2 }}
              onHoverStart={() => setActiveFeature(index)}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Simplified Footer */}
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

export default HomePage;