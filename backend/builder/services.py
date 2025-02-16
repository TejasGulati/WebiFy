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
import os
from typing import Dict, Any, Optional, List, Union, Tuple
from bs4 import BeautifulSoup
import re
from icrawler.builtin import GoogleImageCrawler
import glob
import random
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 3600
DEFAULT_MODEL = 'gemini-pro'
MAX_RETRIES = 3
TIMEOUT = 30
BATCH_SIZE = 3
MIN_CONTENT_LENGTH = 100

@dataclass
class WebsiteStructure:
    components: List[str] = field(default_factory=list)
    colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "blue-600",
        "secondary": "gray-600",
        "accent": "emerald-500",
        "background": "white",
        "text": "gray-900"
    })
    typography: Dict[str, Any] = field(default_factory=lambda: {
        "fonts": ["inter", "system-ui", "sans-serif"],
        "sizes": {
            "base": "text-base",
            "h1": "text-4xl",
            "h2": "text-3xl",
            "h3": "text-2xl",
            "small": "text-sm"
        },
        "weights": {
            "normal": "font-normal",
            "medium": "font-medium",
            "bold": "font-bold"
        }
    })
    spacing: Dict[str, str] = field(default_factory=lambda: {
        "base": "4",
        "small": "2",
        "large": "8",
        "section": "16"
    })
    breakpoints: Dict[str, str] = field(default_factory=lambda: {
        "mobile": "sm",
        "tablet": "md",
        "desktop": "lg",
        "wide": "xl"
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

class ImageHandler:
    def __init__(self, base_dir: str = "./images"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def download_images(self, context: str, num_images: int = 3) -> List[str]:
        try:
            # Clean context for folder name
            folder_name = re.sub(r'[^\w\s-]', '', context).strip().replace(' ', '_')
            save_dir = os.path.join(self.base_dir, folder_name)
            
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Check if we already have enough images
            existing_images = glob.glob(os.path.join(save_dir, "*.jpg"))
            if len(existing_images) >= num_images:
                self.logger.info(f"Using existing images for {context}")
                # Return URLs instead of file paths
                return [f"/images/{folder_name}/{os.path.basename(img)}" for img in random.sample(existing_images, num_images)]
            
            # Download new images
            google_crawler = GoogleImageCrawler(storage={"root_dir": save_dir})
            google_crawler.crawl(keyword=context, max_num=num_images)
            
            # Get all downloaded image paths and convert to URLs
            downloaded_images = glob.glob(os.path.join(save_dir, "*.jpg"))
            if not downloaded_images:
                raise Exception(f"No images downloaded for context: {context}")
                
            # Convert file paths to URLs
            image_urls = [f"/images/{folder_name}/{os.path.basename(img)}" for img in downloaded_images[:num_images]]
            
            self.logger.info(f"Successfully downloaded {len(downloaded_images)} images for {context}")
            return image_urls
            
        except Exception as e:
            self.logger.error(f"Error downloading images for {context}: {str(e)}")
            return []

    def get_context_from_alt(self, alt_text: str) -> str:
        """
        Extracts search context from image alt text.
        
        Args:
            alt_text (str): Alt text from image tag
            
        Returns:
            str: Search context for image
        """
        # Remove common words and clean up the alt text
        common_words = {'image', 'picture', 'photo', 'of', 'the', 'a', 'an'}
        words = alt_text.lower().split()
        context = ' '.join(word for word in words if word not in common_words)
        return context.strip()


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
        self.image_handler = ImageHandler()

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


    
    def _extract_components(self, html: str) -> List[Dict[str, Any]]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            components = []
            for element in soup.find_all(True):
                if element.name in ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']:
                    component = {
                        'type': element.name,
                        'id': element.get('id', ''),
                        'classes': element.get('class', []),
                        'data_attributes': {k: v for k, v in element.attrs.items() if k.startswith('data-')},
                        'children': [child.name for child in element.find_all(True)]
                    }
                    components.append(component)
            return components
        except Exception as e:
            return []
    
    def _clean_html(self, html: str) -> str:
        """Enhanced HTML cleaning with real image integration."""
        if not html:
            return ""
    
        html = re.sub(r'```(?:html)?\n?|\n?```', '', html.strip())
    
        try:
            soup = BeautifulSoup(html, 'html.parser')
        
        # Process each image tag
            for img in soup.find_all('img'):
                alt_text = img.get('alt', '').strip()
                if not alt_text:
                    continue
            
            # Get context and download images
                context = self.image_handler.get_context_from_alt(alt_text)
                image_paths = self.image_handler.download_images(context)
            
                if image_paths:
                # Update image source with correct path
                # Remove any leading slashes and use a clean relative path
                    img['src'] = image_paths[0].lstrip('/')  # This will give us "images/folder/file.jpg"

                # Add appropriate Tailwind classes based on context
                    if 'logo' in alt_text.lower():
                        img['class'] = 'h-12 w-auto'
                    elif 'hero' in alt_text.lower():
                        img['class'] = 'w-full h-[600px] object-cover'
                    elif 'profile' in alt_text.lower():
                        img['class'] = 'h-24 w-24 rounded-full object-cover'
                    else:
                        img['class'] = 'w-full h-64 object-cover rounded-lg'
            
            # Update common components with Tailwind classes
            component_classes = {
                'header': 'bg-white shadow-sm',
                'nav': 'container mx-auto px-4 py-6',
                'main': 'container mx-auto px-4 py-8',
                'section': 'py-16',
                'article': 'prose lg:prose-xl mx-auto',
                'footer': 'bg-gray-50 border-t'
            }
            
            for tag, classes in component_classes.items():
                for element in soup.find_all(tag):
                    existing_classes = element.get('class', [])
                    if isinstance(existing_classes, str):
                        existing_classes = [existing_classes]
                    new_classes = classes.split()
                    element['class'] = existing_classes + new_classes
            
            body_content = str(soup.body) if soup.body else str(soup)
            body_content = re.sub(r'</?body[^>]*>', '', body_content)
            
            title = soup.title.string if soup.title else 'Modern Website'
            
            html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="min-h-screen bg-white dark:bg-gray-900">
    <div class="flex flex-col min-h-screen">
        {body_content}
    </div>
</body>
</html>'''
            
            return html
            
        except Exception as e:
            self.logger.error(f"HTML cleaning failed: {str(e)}")
            return html

    def generate_html(self, description: str) -> Dict[str, Any]:
        """Generate HTML with integrated image handling."""
        if not description:
            self.current_state.errors.append("No description provided")
            return {"status": "error", "message": "No description provided"}
        
        try:
            components = json.dumps(self.current_state.structure.components if self.current_state.structure else [])
            
            # Enhanced prompt to generate meaningful alt text
            html_prompt = f'''Create a modern website using Tailwind CSS for: {description}
                Components: {components}
                Requirements:
                - Use descriptive alt text for images that clearly describes the content
                - Include relevant images for: company logo, hero section, team profiles, product showcases
                - Ensure alt text is meaningful and helps with image search context
                Other requirements remain the same as before...
                '''
            
            content = self._generate_content(html_prompt)
            cleaned_html = self._clean_html(content)
            
            self._validate_and_enhance_structure()
            
            self.current_state.components = self._extract_components(cleaned_html)
            self.current_state.html = cleaned_html
            self.current_state.progress = 50
            
            return {
                "status": "success", 
                "html": cleaned_html, 
                "components": self.current_state.components,
                "warnings": self.current_state.warnings
            }
            
        except Exception as e:
            error_msg = f"HTML generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def generate_css(self, description: str) -> Dict[str, Any]:
        """Generate complementary CSS for Tailwind customization."""
        if not self.current_state.html:
            self.current_state.errors.append("HTML must be generated before CSS")
            return {"status": "error", "message": "HTML generation required first"}
        
        try:
            css_prompt = f"""Create custom CSS to enhance Tailwind styling (only for custom components not covered by Tailwind):
                Requirements:
                - Minimize custom CSS, prefer Tailwind utilities
                - Only add styles for custom animations
                - Add styles for custom gradients if needed
                - Include custom scroll behavior
                - Add any necessary keyframe animations
                """
            
            content = self._generate_content(css_prompt)
            self.current_state.css = self._clean_css(content)
            self.current_state.progress = 75
            return {"status": "success", "css": self.current_state.css}
        except Exception as e:
            error_msg = f"CSS generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def generate_js(self, description: str) -> Dict[str, Any]:
        """Generate JavaScript for enhanced interactivity."""
        if not self.current_state.html:
            self.current_state.errors.append("HTML must be generated before JavaScript")
            return {"status": "error", "message": "HTML generation required first"}
        
        try:
            js_prompt = f"""Create JavaScript to enhance website functionality:
                Requirements:
                - Implement smooth scroll behavior
                - Add intersection observer for animations
                - Implement dark mode toggle
                - Add mobile menu functionality
                - Implement form validation
                - Add lazy loading for images
                - Implement scroll-to-top functionality
                - Add custom animations on scroll
                """
            
            content = self._generate_content(js_prompt)
            js_content = """// Website enhancement functions...""" + content
            self.current_state.js = self._clean_js(js_content)
            self.current_state.progress = 100
            return {"status": "success", "js": self.current_state.js}
        except Exception as e:
            error_msg = f"JavaScript generation failed: {str(e)}"
            self.current_state.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def _validate_and_enhance_structure(self) -> None:
        """Validate component structure and enhance spacing."""
        try:
            if not self.current_state.html:
                return
            
            soup = BeautifulSoup(self.current_state.html, 'html.parser')
            
            # Validate required components
            required_components = set(self.current_state.structure.components if self.current_state.structure else [])
            found_components = {tag.name for tag in soup.find_all(True)}
            missing_components = required_components - found_components
            
            if missing_components:
                self.current_state.warnings.append(f"Missing components: {', '.join(missing_components)}")
        
        except Exception as e:
            self.current_state.warnings.append(f"Structure validation failed: {str(e)}")

    def _initialize_prompts(self):
        """Initialize enhanced prompts with comprehensive guidance."""
        self.prompts = {
        'structure': """Analyze this website description and return a valid JSON structure.
            Description: {description}
            
            IMPORTANT: Create a cohesive, modern website structure following these guidelines:
            1. Color System:
                - Primary: Bold, memorable brand color (#...)
                - Secondary: Complementary shade (#...)
                - Accent: Attention-grabbing highlights (#...)
                - Background: Light/dark variants (#...)
                - Text: Multiple contrast levels (#...)
                All colors must be WCAG 2.1 AA compliant.
            
            2. Typography:
                - Heading Font: Modern, distinctive
                - Body Font: Highly readable
                - Font Sizes: Responsive scales
                - Line Heights: Optimal readability
                - Weights: Clear hierarchy
            
            3. Spacing:
                - Base: Consistent rhythm (1rem)
                - Small: Tight spacing (0.5rem)
                - Large: Section breaks (2rem)
                - Component: Internal spacing (1.5rem)
            
            Return this exact JSON structure:
            {{
                "components": ["header", "nav", "hero", "features", "content", "cta", "footer"],
                "colors": {{
                    "primary": "#hex",
                    "secondary": "#hex",
                    "accent": "#hex",
                    "background": {{
                        "light": "#hex",
                        "dark": "#hex"
                    }},
                    "text": {{
                        "primary": "#hex",
                        "secondary": "#hex"
                    }}
                }},
                "typography": {{
                    "fonts": {{
                        "heading": "font-family",
                        "body": "font-family"
                    }},
                    "sizes": {{
                        "base": {{"size": "1rem", "lineHeight": "1.5"}},
                        "h1": {{"size": "2.5rem", "lineHeight": "1.2"}},
                        "h2": {{"size": "2rem", "lineHeight": "1.3"}},
                        "h3": {{"size": "1.75rem", "lineHeight": "1.4"}},
                        "small": {{"size": "0.875rem", "lineHeight": "1.4"}}
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
                    "section": "4rem",
                    "component": "1.5rem"
                }},
                "breakpoints": {{
                    "mobile": "640px",
                    "tablet": "768px",
                    "desktop": "1024px",
                    "wide": "1280px"
                }}
            }}""",
        
        'html': """Create semantic HTML5 with Tailwind CSS for: {description}
            Structure: {structure}
            
            CRITICAL REQUIREMENTS:
            1. Layout:
                - Sticky header with smooth backdrop blur
                - Hero with overlapping elements
                - Feature grid with hover effects
                - Testimonial carousel
                - CTA with gradient background
                - Fancy list styling
            
            2. Components (implement ALL):
                - Mobile hamburger menu
                - Search bar with autocomplete
                - Newsletter signup form
                - Social proof section
                - FAQ accordion
                - Contact form
            
            3. Must Include:
                - All specified colors from structure
                - Font sizes and weights
                - Proper heading hierarchy
                - Consistent spacing
                - Responsive design
                - Loading states
            
            4. Accessibility:
                - Semantic HTML5 elements
                - ARIA labels
                - Role attributes
                - Screen reader text
                - Skip links
                - Keyboard navigation""",
        
        'css': """Create modern CSS to enhance Tailwind for: {description}
            Structure: {structure}
            
            CRITICAL FEATURES:
            1. Advanced Effects:
                - Smooth backdrop blur
                - Glass morphism
                - Advanced gradients
                - Custom shapes/curves
                - Parallax scrolling
            
            2. Animations:
                - Fade in on scroll
                - Hover transitions
                - Loading states
                - Page transitions
                - Micro-interactions
            
            3. Dark Mode:
                - System preference detection
                - Manual toggle
                - Smooth transition
                - Custom dark palette
            
            4. Performance:
                - Container queries
                - Content-visibility
                - will-change hints
                - GPU acceleration
                - Print styles""",
        
        'js': """Create modern JS functionality for: {description}
            Structure: {structure}
            
            CRITICAL FEATURES:
            1. Interactions:
                - Smooth scroll navigation
                - Mobile menu animations
                - Form validation with error states
                - Dark mode toggle with storage
                - Lazy loading with blur up
                - Intersection observers
            
            2. Advanced Features:
                - State management
                - Form autosave
                - Search autocomplete
                - Infinite scroll
                - Progress indicators
            
            3. Performance:
                - Debounced scroll
                - Throttled resize
                - RAF animations
                - Asset preloading
                - Error boundaries
            
            4. Must Include:
                - TypeScript-like types
                - Error handling
                - Loading states
                - Console warnings
                - Cleanup functions"""
    }


    

    
    def _validate_sync(self) -> List[str]:
        warnings = []
        try:
            soup = BeautifulSoup(self.current_state.html, 'html.parser')
            html_classes = {cls for element in soup.find_all(True) for cls in element.get('class', [])}
            html_ids = {element.get('id') for element in soup.find_all(True) if element.get('id')}
            css_classes = set(re.findall(r'\.([\w-]+)', self.current_state.css))
            css_ids = set(re.findall(r'#([\w-]+)', self.current_state.css))
            js_classes = set(re.findall(r'getElementsByClassName\([\'\"](.+?)[\'\"]\)', self.current_state.js))
            js_ids = set(re.findall(r'getElementById\([\'\"](.+?)[\'\"]\)', self.current_state.js))
            
            for css_class in css_classes:
                if css_class not in html_classes:
                    warnings.append(f"CSS class '{css_class}' not found in HTML")
            for js_class in js_classes:
                if js_class not in html_classes:
                    warnings.append(f"JavaScript class reference '{js_class}' not found in HTML")
            for js_id in js_ids:
                if js_id not in html_ids:
                    warnings.append(f"JavaScript ID reference '{js_id}' not found in HTML")
            
            return warnings
        except Exception as e:
            return [f"Sync validation error: {str(e)}"]
        
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
