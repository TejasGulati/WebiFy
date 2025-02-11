from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from typing import Dict, Any
import logging
from .services import process_generation, WebsiteGenerator, GenerationState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 3600  # 1 hour

@api_view(['POST'])
def process_prompt(request) -> Response:
    """
    Process website generation prompt and maintain state across requests.
    
    Args:
        request: HTTP request object containing:
            - prompt (str): Description of the website to generate
            - reset (bool, optional): Whether to reset the current generation state
            
    Returns:
        Response: JSON response containing generation results and current state
    """
    prompt = request.data.get('prompt', '')
    reset = request.data.get('reset', False)
    session_id = request.session.session_key or 'default'
    
    if not prompt:
        return Response({
            'error': 'No prompt provided',
            'status': 'error'
        }, status=400)
        
    try:
        # Get or initialize generation state
        cache_key = f'website_state_{session_id}'
        current_state = {} if reset else cache.get(cache_key, {})
        
        # Process the generation step
        result = process_generation(prompt, current_state)
        
        # Store updated state
        if result.get('current_state'):
            cache.set(cache_key, result['current_state'], timeout=CACHE_TIMEOUT)
            
        # Prepare response data
        response_data = {
            'status': 'success',
            'thought': result.get('thought', ''),
            'response': result.get('response', ''),
            'progress': result.get('current_state', {}).get('progress', 0),
            'completed': result.get('completed', False)
        }
        
        # Include generated assets if available
        current_state = result.get('current_state', {})
        if current_state.get('html'):
            response_data['html'] = current_state['html']
        if current_state.get('css'):
            response_data['css'] = current_state['css']
        if current_state.get('js'):
            response_data['js'] = current_state['js']
        if current_state.get('structure'):
            response_data['structure'] = current_state['structure']
            
        # Include any errors or warnings
        if result.get('errors'):
            response_data['errors'] = result['errors']
        if result.get('warnings'):
            response_data['warnings'] = result['warnings']
            
        # Include generation time if available
        if current_state.get('generation_start') and current_state.get('generation_end'):
            response_data['generation_time'] = current_state['generation_end'] - current_state['generation_start']
            
        return Response(response_data)
        
    except Exception as e:
        error_msg = f"Error processing prompt: {str(e)}"
        logger.error(error_msg)
        return Response({
            'error': error_msg,
            'status': 'error'
        }, status=500)

@api_view(['POST'])
def reset_generation(request) -> Response:
    """
    Reset the website generation state for the current session.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: JSON response confirming the reset
    """
    try:
        session_id = request.session.session_key or 'default'
        cache_key = f'website_state_{session_id}'
        
        # Clear the cached state
        cache.delete(cache_key)
        
        return Response({
            'message': 'Generation state reset successfully',
            'status': 'success'
        })
        
    except Exception as e:
        error_msg = f"Error resetting generation state: {str(e)}"
        logger.error(error_msg)
        return Response({
            'error': error_msg,
            'status': 'error'
        }, status=500)

@api_view(['GET'])
def get_generation_state(request) -> Response:
    """
    Retrieve the current generation state for the session.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: JSON response containing the current generation state
    """
    try:
        session_id = request.session.session_key or 'default'
        cache_key = f'website_state_{session_id}'
        
        # Get current state from cache
        current_state = cache.get(cache_key, {})
        
        return Response({
            'status': 'success',
            'state': current_state
        })
        
    except Exception as e:
        error_msg = f"Error retrieving generation state: {str(e)}"
        logger.error(error_msg)
        return Response({
            'error': error_msg,
            'status': 'error'
        }, status=500)