from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from .services import process_generation

@api_view(['POST'])
def process_prompt(request):
    """
    Process website generation prompt and maintain state across requests.
    Expects JSON input with 'prompt' field and optional 'reset' flag.
    """
    prompt = request.data.get('prompt', '')
    reset = request.data.get('reset', False)
    session_id = request.session.session_key or 'default'

    if not prompt:
        return Response({'error': 'No prompt provided'}, status=400)

    try:
        # Get current state from cache or initialize new
        current_state = {} if reset else cache.get(f'website_state_{session_id}', {})

        # Process the generation step
        result = process_generation(prompt, current_state)

        # Store updated state in cache
        cache.set(f'website_state_{session_id}', result['current_state'], timeout=3600)

        # Prepare response based on current state and completion
        response_data = {
            'thought': result['thought'],
            'response': result['response'],
            'progress': result['current_state'].get('progress', 0),
            'completed': result.get('completed', False),
        }

        # Include generated assets if available
        if result['current_state'].get('html'):
            response_data['html'] = result['current_state']['html']
        if result['current_state'].get('css'):
            response_data['css'] = result['current_state']['css']
        if result['current_state'].get('js'):
            response_data['js'] = result['current_state']['js']
        if result['current_state'].get('structure'):
            response_data['structure'] = result['current_state']['structure']

        # Include any errors
        if 'errors' in result:
            response_data['errors'] = result['errors']

        return Response(response_data)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=500)

@api_view(['POST'])
def reset_generation(request):
    """
    Reset the website generation state for the current session.
    """
    session_id = request.session.session_key or 'default'
    cache.delete(f'website_state_{session_id}')
    return Response({
        'message': 'Generation state reset successfully',
        'status': 'success'
    })