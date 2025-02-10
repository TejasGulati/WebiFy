import google.generativeai as genai
from django.conf import settings

import re  # Add this import at the top if not already present

def generate_website_code(prompt):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    response = model.generate_content(
        f"""Convert this website description to raw HTML and CSS code:
        {prompt}
        
        IMPORTANT:
        1. Return ONLY valid HTML code.
        2. DO NOT include markdown syntax (no triple backticks).
        3. Include inline CSS styles where appropriate.
        """
    )
    
    # Clean the markdown (remove triple backticks and 'html')
    cleaned_code = re.sub(r'```html|```', '', response.text).strip()
    return cleaned_code
