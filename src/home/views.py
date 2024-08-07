from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from urllib.parse import urlparse, parse_qs
from django.views.decorators.csrf import csrf_exempt
import json
from . import falcon
from .falcon import task_statuses, task_context, start_voiceover_generation
from .models import TaskStatus

# Create your views here.
language_dict = {
    'en': 'English',
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'it': 'Italian',
    'ru': 'Russian',
    'ja': 'Japanese',
    'cs': 'Czech',
    'pt': 'Portuguese'
}

def home_page(request):
    return render(request, 'index.html')

def validate_parameters(request):
    yt_link = request.GET.get('link')
    target_language = request.GET.get('language')
    voiceover_gender = request.GET.get('voiceoverGender')
    quizLang = request.GET.get('quizLang')
    
    if not yt_link or not target_language:
        return None, JsonResponse({"Error": "Missing 'link' or 'language' parameter"}, status=400)

    target_language_code = language_dict.get(target_language)

    try:
        vid = parse_qs(urlparse(yt_link).query)['v'][0]
    except KeyError:
        return None, JsonResponse({"Error": "Invalid Youtube Link"}, status=400)

    return (vid, target_language_code, voiceover_gender, quizLang), None

@csrf_exempt
def watch(request):
    params, error = validate_parameters(request)
    print("before error check")
    if error:
        return error
    print("after error")
    vid, target_language, voiceover_gender, quizLang = params
    
    task_id = start_voiceover_generation(vid, target_language, voiceover_gender, quizLang, TaskStatus)
    print("after start voiceover generation")
    return JsonResponse({'status': 'Starting Voiceover Generation...', 'task_id': task_id})


@csrf_exempt
def task_status(request, task_id):
    task = TaskStatus.objects.get(task_id=task_id)
    print(task.status)
    return JsonResponse({'status': task.status})
    
@csrf_exempt
def watch_webpage(request, task_id):
    task = TaskStatus.objects.get(task_id=task_id)
    return render(request, 'watch.html', task.context)

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('content')
            groupedSentences = json.loads(data.get('groupedSentences'))
            messageHistory = json.loads(data.get('messageHistory'))
            
            # Process the message with your chatbot logic
            response_message = falcon.askQnA(groupedSentences, messageHistory, user_message)
            return JsonResponse({'content': response_message})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def quiz(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            groupedSentences = json.loads(data.get('groupedSentences'))
            targetLang = data.get('targetLang')
            quizLang = targetLang if data.get('quizLang') == 'translated' else "English"
            
            # Process the message with your chatbot logic
            response_message = falcon.quizMCQ(groupedSentences, quizLang)
            print(response_message)
            return JsonResponse({'content': response_message})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

