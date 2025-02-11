import os
from typing import Dict, Any, Optional, List, Union
import json
import re
from datetime import datetime
import time
from dataclasses import dataclass, asdict, field
import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor
import logging
import asyncio
from bs4 import BeautifulSoup
import html.parser
import cssbeautifier
import jsbeautifier
from dotenv import load_dotenv

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Extended constants
CACHE_TIMEOUT = 3600  # 1 hour
DEFAULT_MODEL = 'gemini-pro'
MAX_RETRIES = 3
TIMEOUT = 30  # seconds
BATCH_SIZE = 3  # For chunked generation
MIN_CONTENT_LENGTH = 100  # Minimum expected content length

@dataclass
class WebsiteStructure:
    components: List[str] = field(default_factory=list)
    colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#007bff",
        "secondary": "#6c757d",
        "accent": "#28a745",
        "background": "#ffffff",
        "text": "#212529"
    })
    typography: Dict[str, Any] = field(default_factory=lambda: {
        "fonts": ["system-ui", "-apple-system", "sans-serif"],
        "sizes": {
            "base": "16px",
            "h1": "2.5rem",
            "h2": "2rem",
            "h3": "1.75rem",
            "small": "0.875rem"
        },
        "weights": {
            "normal": "400",
            "medium": "500",
            "bold": "700"
        }
    })
    spacing: Dict[str, str] = field(default_factory=lambda: {
        "base": "1rem",
        "small": "0.5rem",
        "large": "2rem",
        "section": "4rem"
    })
    breakpoints: Dict[str, str] = field(default_factory=lambda: {
        "mobile": "576px",
        "tablet": "768px",
        "desktop": "1024px",
        "wide": "1200px"
    })

@dataclass
class GenerationState:
    structure: Optional[WebsiteStructure] = None
    html: str = ""
    css: str = ""
    js: str = ""
    components: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    progress: int = 0
    completed: bool = False
    generation_start: Optional[float] = None
    generation_end: Optional[float] = None

class WebsiteGenerator:
    """Enhanced service for generating website code using AI."""
    
    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize the generator with enhanced configuration."""
        load_dotenv() 
        self.current_state = GenerationState()
        self.current_year = datetime.now().year
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._initialize_prompts()
        self._initialize_api(model)

    def _initialize_api(self, model: str) -> None:
        """Initialize the API with enhanced error handling and fallback mechanism."""
        api_keys = [
            os.getenv(f'GEMINI_API_KEY{i}') 
            for i in range(1, 4)
        ]
        api_keys = [key for key in api_keys if key]

        if not api_keys:
            raise ValueError("No API keys configured. Please set GEMINI_API_KEY1, GEMINI_API_KEY2, etc. in .env.")

        for api_key in api_keys:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model)
                logger.info(f"Successfully initialized Gemini API with key ending in {api_key[-4:]}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize with API key ending in {api_key[-4:]}: {str(e)}")
                continue

        raise ValueError("Failed to initialize with all available API keys.")
        
    def _initialize_prompts(self):
        """Initialize enhanced prompts with comprehensive guidance."""
        self.prompts = {
            'structure': """Analyze this website description and return a valid JSON structure.
                Description: {description}
                
                Return a JSON object with:
                {{
                    "components": ["list", "of", "semantic", "components"],
                    "colors": {{
                        "primary": "#hex",
                        "secondary": "#hex",
                        "accent": "#hex",
                        "background": "#hex",
                        "text": "#hex"
                    }},
                    "typography": {{
                        "fonts": ["primary-font", "fallback-font"],
                        "sizes": {{
                            "base": "16px",
                            "h1": "2.5rem",
                            "h2": "2rem",
                            "h3": "1.75rem",
                            "small": "0.875rem"
                        }},
                        "weights": {{
                            "normal": "400",
                            "medium": "500",
                            "bold": "700"
                        }}
                    }},
                    "spacing": {{
                        "base": "1rem",
                        "small": "0.5rem",
                        "large": "2rem",
                        "section": "4rem"
                    }},
                    "breakpoints": {{
                        "mobile": "576px",
                        "tablet": "768px",
                        "desktop": "1024px",
                        "wide": "1200px"
                    }}
                }}""",
            
            'html': """Create semantic HTML5 for: {description}
                Components: {components}
                Requirements: 
                - Use semantic HTML5 elements (<header>, <nav>, <main>, <section>, <article>, <footer>)
                - Include ARIA labels and roles for accessibility
                - Add comprehensive meta tags including Open Graph
                - Ensure proper heading hierarchy
                - Use BEM naming convention consistently
                - Include data-testid attributes for testing
                - Add schema.org structured data
                - Implement responsive images with srcset
                - Include proper alt text for all images
                - Add support for dark mode
                - Include print-friendly structure""",
            
            'css': """Create modern CSS for: {description}
                Structure: {structure}
                Requirements:
                - Define CSS custom properties for colors, typography, spacing
                - Implement mobile-first responsive design
                - Use modern layout techniques (Grid, Flexbox)
                - Add smooth transitions and animations
                - Implement proper hover and focus states
                - Follow BEM methodology strictly
                - Include print styles
                - Add fallbacks for older browsers
                - Optimize performance with will-change
                - Implement dark mode support
                - Use logical properties (margin-block, padding-inline)
                - Include accessibility enhancements""",
            
            'js': """Create modern JS for: {description}
                Requirements:
                - Use ES6+ features (async/await, destructuring, modules)
                - Implement proper form validation with error messages
                - Add smooth scrolling and intersection observers
                - Include proper error handling and logging
                - Implement lazy loading for images
                - Add service worker for offline support
                - Use event delegation for performance
                - Implement proper touch support
                - Add keyboard navigation
                - Include analytics tracking
                - Implement dark mode toggle
                - Add performance monitoring"""
        }

    def _generate_with_retry(self, prompt: str, retries: int = MAX_RETRIES) -> str:
        """Enhanced generation with better error handling and validation."""
        last_error = None
        backoff_factor = 1.5
        
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                
                if not response or not hasattr(response, 'text'):
                    raise ValueError("Invalid response structure")
                    
                content = response.text.strip()
                if len(content) < MIN_CONTENT_LENGTH:
                    raise ValueError(f"Generated content too short: {len(content)} chars")
                    
                return content
                
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < retries - 1:
                    wait_time = (backoff_factor ** attempt) * 1
                    time.sleep(wait_time)
                continue
                
        raise RuntimeError(f"Generation failed after {retries} attempts. Last error: {str(last_error)}")

    def _generate_content(self, prompt: str) -> str:
        """Generate content using AI model with enhanced caching, validation and batch processing."""
        if not prompt:
            raise ValueError("Empty prompt provided")
        
        cache_key = f"website_gen_{hash(prompt)}"
        cached_response = cache.get(cache_key)
    
        if cached_response:
            logger.info("Retrieved response from cache")
            return cached_response
        
        try:
        # Split long prompts into batches if needed
            if len(prompt) > 4000:  # Assuming 4000 chars as batch size
                chunks = [prompt[i:i + 4000] for i in range(0, len(prompt), 4000)]
                content = ""
            
                for chunk in chunks:
                    chunk_content = self._generate_with_retry(chunk)
                    content += chunk_content
                
            # Allow a small delay between chunks
                time.sleep(0.5)
            else:
                content = self._generate_with_retry(prompt)
        
            if len(content) < MIN_CONTENT_LENGTH:
                raise ValueError(f"Generated content too short: {len(content)} chars")
            
            cache.set(cache_key, content, CACHE_TIMEOUT)
            return content
        
        except Exception as e:
            error_msg = f"Content generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            logger.error(error_msg)
            raise

    def _validate_and_clean_json(self, content: str) -> Dict:
        """Enhanced JSON validation and cleaning."""
        try:
            data = json.loads(content)
            
            # Validate required structure
            required_keys = ['components', 'colors', 'typography', 'spacing', 'breakpoints']
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")
                
            return data
            
        except json.JSONDecodeError:
            # Attempt to extract JSON from text
            json_match = re.search(r'({[\s\S]*})', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
        # Return default structure if parsing fails
        return {
            "components": ["header", "main", "footer"],
            "colors": {
                "primary": "#007bff",
                "secondary": "#6c757d",
                "accent": "#28a745",
                "background": "#ffffff",
                "text": "#212529"
            },
            "typography": {
                "fonts": ["system-ui", "sans-serif"],
                "sizes": {
                    "base": "16px",
                    "h1": "2.5rem",
                    "h2": "2rem",
                    "h3": "1.75rem",
                    "small": "0.875rem"
                },
                "weights": {
                    "normal": "400",
                    "medium": "500",
                    "bold": "700"
                }
            },
            "spacing": {
                "base": "1rem",
                "small": "0.5rem",
                "large": "2rem",
                "section": "4rem"
            },
            "breakpoints": {
                "mobile": "576px",
                "tablet": "768px",
                "desktop": "1024px",
                "wide": "1200px"
            }
        }

    def _clean_html(self, html: str) -> str:
        """Enhanced HTML cleaning with meta tags, schema.org, and Open Graph support."""
        if not html:
            return ""
        
    # Remove code blocks
        html = re.sub(r'```(?:html)?\n?|\n?```', '', html.strip())
    
    # Fix common issues
        html = re.sub(r'&copy; \d{4}', f'&copy; {self.current_year}', html)
        html = re.sub(r'style="[^"]*"', '', html)  # Remove inline styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)  # Remove inline scripts
    
    # Ensure proper DOCTYPE
        if '<!DOCTYPE html>' not in html:
            html = '<!DOCTYPE html>\n' + html
        
    # Validate structure
        try:
            soup = BeautifulSoup(html, 'html.parser')
            if not soup.html or not soup.head or not soup.body:
                raise ValueError("Invalid HTML structure")
        
        # Add required meta tags if missing
            head = soup.head
        
        # Basic meta tags
            required_meta = {
            'charset': {'charset': 'utf-8'},
            'viewport': {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'},
            'description': {'name': 'description', 'content': 'Website generated with AI assistance'},
            'color-scheme': {'name': 'color-scheme', 'content': 'light dark'}
        }
        
            for meta_type, attrs in required_meta.items():
                if not soup.find('meta', attrs=attrs):
                    meta = soup.new_tag('meta')
                    for attr, value in attrs.items():
                        meta[attr] = value
                    head.append(meta)
        
        # Open Graph meta tags
            og_meta = {
            'og:type': 'website',
            'og:title': soup.title.string if soup.title else 'Generated Website',
            'og:description': 'Website generated with AI assistance',
            'og:image': '/api/placeholder/1200/630',  # Placeholder image
            'og:url': '{{request.build_absolute_uri}}'  # Template variable to be replaced
        }
        
            for og_prop, content in og_meta.items():
                if not soup.find('meta', property=og_prop):
                    meta = soup.new_tag('meta')
                    meta['property'] = og_prop
                    meta['content'] = content
                    head.append(meta)
        
        # Add basic Schema.org structured data
            if not soup.find('script', type='application/ld+json'):
                schema_data = {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": soup.title.string if soup.title else 'Generated Website',
                "description": "Website generated with AI assistance",
                "url": "{{request.build_absolute_uri}}",  # Template variable to be replaced
                "dateModified": datetime.now().isoformat()
            }
            
                schema_script = soup.new_tag('script')
                schema_script['type'] = 'application/ld+json'
                schema_script.string = json.dumps(schema_data, indent=2)
                head.append(schema_script)
        
            return soup.prettify()
        
        except Exception as e:
            logger.error(f"HTML validation failed: {str(e)}")
            return html

    def _clean_css(self, css: str) -> str:
        """Enhanced CSS cleaning and formatting."""
        if not css:
            return ""
            
        # Remove code blocks
        css = re.sub(r'```(?:css)?\n?|\n?```', '', css.strip())
        
        try:
            # Use cssbeautifier for consistent formatting
            css = cssbeautifier.beautify(css, {
                'indent_size': 2,
                'indent_char': ' ',
                'preserve_newlines': True,
                'max_preserve_newlines': 2
            })
            
            # Add dark mode support if not present
            if '@media (prefers-color-scheme: dark)' not in css:
                css += '\n\n@media (prefers-color-scheme: dark) {\n  :root {\n    /* Dark mode variables */\n  }\n}'
                
            # Add print styles if not present
            if '@media print' not in css:
                css += '\n\n@media print {\n  /* Print styles */\n}'
                
            return css
            
        except Exception as e:
            logger.error(f"CSS formatting failed: {str(e)}")
            return css

    def _clean_js(self, js: str) -> str:
        """Enhanced JavaScript cleaning and formatting."""
        if not js:
            return ""
            
        # Remove code blocks
        js = re.sub(r'```(?:js|javascript)?\n?|\n?```', '', js.strip())
        
        try:
            # Use jsbeautifier for consistent formatting
            js = jsbeautifier.beautify(js, {
                'indent_size': 2,
                'indent_char': ' ',
                'preserve_newlines': True,
                'max_preserve_newlines': 2,
                'space_after_anon_function': True,
                'space_in_empty_paren': False
            })
            
            # Add use strict directive if not present
            if '"use strict";' not in js and "'use strict';" not in js:
                js = '"use strict";\n\n' + js
                
            return js
            
        except Exception as e:
            logger.error(f"JavaScript formatting failed: {str(e)}")
            return js

    async def generate_website(self, description: str) -> Dict[str, Any]:
        """Enhanced website generation with better parallelization and error handling."""
        try:
            self.current_state = GenerationState()
            self.current_state.generation_start = time.time()
            
            # Create tasks for concurrent generation
            tasks = []
            with ThreadPoolExecutor() as executor:
                # First phase: Structure analysis
                structure_future = executor.submit(self.analyze_structure, description)
                structure_result = await asyncio.wrap_future(structure_future)
                
                if structure_result.get("status") == "error":
                    raise ValueError(f"Structure analysis failed: {structure_result.get('message')}")
                
                # Second phase: Parallel generation of HTML, CSS, and JS
                html_future = executor.submit(self.generate_html, description)
                css_future = executor.submit(self.generate_css, description)
                js_future = executor.submit(self.generate_js, description)
                
                results = await asyncio.gather(
                    asyncio.wrap_future(html_future),
                    asyncio.wrap_future(css_future),
                    asyncio.wrap_future(js_future)
                )
                
                # Validate results
                for result in results:
                    if result.get("status") == "error":
                        self.current_state.warnings.append(result.get("message"))
                
            self.current_state.completed = True
            self.current_state.progress = 100
            self.current_state.generation_end = time.time()
            
            generation_time = self.current_state.generation_end - self.current_state.generation_start
            logger.info(f"Website generation completed in {generation_time:.2f} seconds")
            
            return self.get_final_output()
            
        except Exception as e:
            error_msg = f"Website generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "errors": self.current_state.errors,
                "warnings": self.current_state.warnings
            }

    def analyze_structure(self, description: str) -> Dict[str, Any]:
        """Enhanced structure analysis with better validation."""
        if not description:
            self.current_state.errors.append("No description provided")
            return {"status": "error", "message": "No description provided"}
            
        try:
            prompt = self.prompts['structure'].format(description=description)
            content = self._generate_content(prompt)
            
            structure = self._validate_and_clean_json(content)
            
            # Validate required fields
            required_fields = ['components', 'colors', 'typography', 'spacing', 'breakpoints']
            missing_fields = [field for field in required_fields if field not in structure]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            self.current_state.structure = WebsiteStructure(**structure)
            self.current_state.progress = 25
            
            return {"status": "success", "structure": asdict(self.current_state.structure)}
            
        except Exception as e:
            error_msg = f"Structure analysis failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def generate_html(self, description: str) -> Dict[str, Any]:
        """Enhanced HTML generation with better structure and accessibility."""
        if not description:
            self.current_state.errors.append("No description provided")
            return {"status": "error", "message": "No description provided"}
            
        try:
            components = json.dumps(
                self.current_state.structure.components if self.current_state.structure else []
            )
            prompt = self.prompts['html'].format(description=description, components=components)
            
            content = self._generate_content(prompt)
            self.current_state.html = self._clean_html(content)
            self.current_state.progress = 50
            
            return {"status": "success", "html": self.current_state.html}
            
        except Exception as e:
            error_msg = f"HTML generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def generate_css(self, description: str) -> Dict[str, Any]:
        """Enhanced CSS generation with modern features and optimizations."""
        if not description:
            self.current_state.errors.append("No description provided")
            return {"status": "error", "message": "No description provided"}
            
        try:
            structure = asdict(self.current_state.structure) if self.current_state.structure else {}
            prompt = self.prompts['css'].format(
                description=description,
                structure=json.dumps(structure)
            )
            
            content = self._generate_content(prompt)
            self.current_state.css = self._clean_css(content)
            self.current_state.progress = 75
            
            return {"status": "success", "css": self.current_state.css}
            
        except Exception as e:
            error_msg = f"CSS generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def generate_js(self, description: str) -> Dict[str, Any]:
        """Enhanced JavaScript generation with modern features and best practices."""
        if not description:
            self.current_state.errors.append("No description provided")
            return {"status": "error", "message": "No description provided"}
            
        try:
            prompt = self.prompts['js'].format(description=description)
            content = self._generate_content(prompt)
            
            self.current_state.js = self._clean_js(content)
            self.current_state.progress = 100
            
            return {"status": "success", "js": self.current_state.js}
            
        except Exception as e:
            error_msg = f"JavaScript generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def get_final_output(self) -> Dict[str, Any]:
        """Enhanced output generation with validation and optimization."""
        try:
            # Validate and optimize generated code
            html = self._clean_html(self.current_state.html)
            css = self._clean_css(self.current_state.css)
            js = self._clean_js(self.current_state.js)
            
            output = {
                "status": "success" if not self.current_state.errors else "error",
                "html": html,
                "css": css,
                "js": js,
                "structure": asdict(self.current_state.structure) if self.current_state.structure else None,
                "progress": self.current_state.progress,
                "completed": self.current_state.completed,
                "errors": self.current_state.errors,
                "warnings": self.current_state.warnings,
                "generation_time": (
                    self.current_state.generation_end - self.current_state.generation_start
                    if self.current_state.generation_end and self.current_state.generation_start
                    else None
                )
            }
            
            # Validate output completeness
            if not all([html, css, js]):
                output["status"] = "error"
                output["errors"].append("Some required components were not generated")
            
            return output
            
        except Exception as e:
            error_msg = f"Error preparing final output: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "errors": self.current_state.errors + [error_msg],
                "warnings": self.current_state.warnings
            }
        
def process_generation(prompt: str, current_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process website generation with enhanced state management."""
    try:
        generator = WebsiteGenerator()
        
        if current_state:
            if isinstance(current_state, dict):
                structure = current_state.get('structure')
                if structure:
                    current_state['structure'] = WebsiteStructure(**structure)
                generator.current_state = GenerationState(**current_state)
            else:
                generator.current_state = current_state
        
        response = {
            "thought": "",
            "moves": [],
            "response": "",
            "completed": False,
            "errors": generator.current_state.errors,
            "warnings": generator.current_state.warnings,
            "progress": generator.current_state.progress
        }
        
        # Determine next step based on current state
        if not generator.current_state.structure:
            result = generator.analyze_structure(prompt)
            response.update({
                "thought": "Starting structure analysis and component planning",
                "moves": ["analyze_structure"],
                "response": "🔍 Analyzing website structure and planning components..."
            })
        elif not generator.current_state.html:
            result = generator.generate_html(prompt)
            response.update({
                "thought": "Generating semantic HTML structure with accessibility features",
                "moves": ["generate_html"],
                "response": "📝 Creating accessible HTML markup with semantic structure..."
            })
        elif not generator.current_state.css:
            result = generator.generate_css(prompt)
            response.update({
                "thought": "Implementing responsive styles and modern CSS features",
                "moves": ["generate_css"],
                "response": "🎨 Implementing responsive CSS with modern features..."
            })
        elif not generator.current_state.js:
            result = generator.generate_js(prompt)
            response.update({
                "thought": "Adding interactive features and performance optimizations",
                "moves": ["generate_js"],
                "response": "⚡ Adding JavaScript functionality and optimizations..."
            })
        else:
            response.update({
                "thought": "Website generation completed successfully",
                "moves": ["final_output"],
                "response": "🚀 Website generation completed with all features implemented!",
                "completed": True
            })
        
        # Update response with current state and any warnings
        response["current_state"] = asdict(generator.current_state)
        
        if generator.current_state.warnings:
            response["response"] += f"\n⚠️ Note: {len(generator.current_state.warnings)} warning(s) generated."
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Generation process failed: {error_msg}")
        return {
            "thought": "Error encountered during generation process",
            "moves": ["handle_error"],
            "response": f"⚠️ Error: {error_msg}",
            "current_state": asdict(generator.current_state) if generator else {},
            "errors": [error_msg],
            "warnings": generator.current_state.warnings if generator else [],
            "progress": 0,
            "completed": False
        }