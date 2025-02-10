from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import generate_website_code

@api_view(['POST'])
def process_prompt(request):
    prompt = request.data.get('prompt', '')
    if not prompt:
        return Response({'error': 'No prompt provided'}, status=400)

    try:
        generated_code = generate_website_code(prompt)
        return Response({'code': generated_code})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
