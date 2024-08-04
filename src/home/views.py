from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from urllib.parse import urlparse, parse_qs
from django.views.decorators.csrf import csrf_exempt
import json
from . import falcon
from asgiref.sync import sync_to_async

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

async def get_transcript(vid):
    return await sync_to_async(falcon.getTranscript)(vid)

async def get_translated_transcript(grouped_sentences, original_lang, target_lang):
    return await sync_to_async(falcon.getTranslatedTranscript)(grouped_sentences, original_lang, target_lang)

async def get_voiceover(vid, translated_transcript, original_lang, target_lang, voiceover_gender):
    return await sync_to_async(falcon._getVoiceOver)(vid, translated_transcript, original_lang, target_lang, voiceover_gender)

async def watch(request):
    yt_link = request.GET.get('link')
    target_language = request.GET.get('language')
    voiceover_gender = request.GET.get('voiceoverGender')

    if not yt_link or not target_language:
        return HttpResponse("400 - Bad Request: Missing 'link' or 'language' parameter")

    target_language = language_dict.get(target_language)
    if not target_language:
        return HttpResponse("400 - Bad Request: Unsupported language")
    

    try:
        vid = parse_qs(urlparse(yt_link).query)['v'][0]
    except KeyError:
        return HttpResponse("400 - Bad Request: Invalid YouTube link")

    context = {'vid': vid}
    context['targetLang'] = target_language
    
    transcript_response = await get_transcript(vid)
    if not transcript_response[0]:
        return HttpResponse("404 - Transcript not found")

    original_lang = transcript_response[0]
    transcript = transcript_response[1]
    

    grouped_sentences = falcon.groupSentences(transcript)
    context['groupedSentences'] = json.dumps(grouped_sentences)

    if original_lang != target_language:
    
        translated_transcript = await get_translated_transcript(grouped_sentences[:30], original_lang, target_language)
        await get_voiceover(
            vid,
            translated_transcript,
            original_lang,
            target_language,
            0 if voiceover_gender == 'female' else 1
        )
        context['playVoiceover'] = "1"
    else:
        context['playVoiceover'] = "0"


    return render(request, 'watch.html', context)

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
            
            # Process the message with your chatbot logic
            response_message = falcon.quizMCQ(groupedSentences, targetLang)
            print(response_message)
            return JsonResponse({'content': response_message})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

