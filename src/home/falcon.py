import random
from youtube_transcript_api import YouTubeTranscriptApi
from pydub import AudioSegment
from google.cloud import texttospeech
import numpy as np
from ai71 import AI71
from dotenv import dotenv_values, load_dotenv
import json
import re
from deep_translator import GoogleTranslator
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, PermissionDenied, Unauthenticated
import os

load_dotenv()

AI71_API_KEY = os.getenv('AI71_APIKEY_deploy')
client = AI71(AI71_API_KEY)
supportedLang = ['English', 'Hindi', 'Spanish', 'French', 'German', 'Chinese', 'Arabic', 'Italian', 'Russian', 'Japanese', 'Czech', 'Portuguese']

def getTranscript(videoID):

    try:
        transcriptList = YouTubeTranscriptApi.list_transcripts(videoID)

        try:
            # Pick the auto-generated language for the original language
            for transcript in transcriptList:
                if transcript.is_generated:
                    videoLang = str(transcript.language).split()[0]

            # Check for the original language and fetch the transcript
            for transcript in transcriptList:
                if transcript.language.split()[0] == videoLang:
                    print(transcript.fetch())

                    pattern = re.compile(r'\(.*?\)')

                    transcriptOriginal = transcript.fetch()
                    for entry in transcriptOriginal:
                        if 'Transcriber: ' in entry['text']:
                            transcriptOriginal.remove(entry)
                        entry['text'] = entry['text'].replace('\n', ' ')
                        entry['text'] = pattern.sub('', entry['text'])  # Remove text before and including ':'
                        parts = entry['text'].split(':', 1)  # Split text by the first colon only
                        if len(parts) > 1:
                            entry['text'] = parts[1].strip()


                    return videoLang, transcriptOriginal

        except:
            for transcript in transcriptList:
                videoLang = str(transcript.language).split()[0]

                pattern = re.compile(r'\(.*?\)')

                transcriptOriginal = transcript.fetch()
                for entry in transcriptOriginal:
                    if 'Transcriber: ' in entry['text']:
                        transcriptOriginal.remove(entry)
                    entry['text'] = entry['text'].replace('\n', ' ')
                    entry['text'] = pattern.sub('', entry['text'])  # Remove text before and including ':'
                    parts = entry['text'].split(':', 1)  # Split text by the first colon only
                    if len(parts) > 1:
                        entry['text'] = parts[1].strip()

                return videoLang, transcriptOriginal

    except Exception as e:
        return False, None

def groupSentences(transcription):
    #print("In GroupSentences")
    groupedSentences = []
    current_text = ''
    current_start = 0
    current_duration = 0
    sentence_started = False
    special_marker_pattern = re.compile(r'\[[a-zA-Z]*\]|\([a-zA-Z]*\)|[A-Za-z]*:')

    for entry in transcription:
        text = entry['text']
        start = entry['start']
        duration = entry['duration']

        if not sentence_started:
                current_start = start
                sentence_started = True

        
        
        # If the current_text is empty, start a new group
        if not current_text:

            current_text = text
            current_start = start
            current_duration = duration
        else:
            # Append the text to the current group
            current_text += " " + text
            current_duration += duration
        
        if not current_text:
            continue

        if current_text[-1] in '.!?' or special_marker_pattern.fullmatch(text):
            clean_text = special_marker_pattern.sub('', current_text)
            if not clean_text:
                continue
            groupedSentences.append({
                'text': clean_text.strip(),
                'start': current_start,
                'duration': current_duration
            })
            current_text = ''
            current_duration = 0
            sentence_started = False
            
        

    if current_text:  # add any remaining sentence
        groupedSentences.append({
            'text': current_text.strip(),
            'start': current_start,
            'duration': current_duration
        })
    #print(groupedSentences)

    return groupedSentences


def falconTranslate(text, originalLang, targetLang):

    languages = {"Hindi": {"text": "मुझे परियोजना की प्रगति पर एक रिपोर्ट देनी है, जिसमें आई चुनौतियाँ और उन्हें हल करने के तरीके बताने हैं।"},
                 "English": {"text": "I need to submit a comprehensive report on the project's progress, including the challenges faced and the strategies implemented to overcome them."},
                 "Spanish": {"text": "Debo presentar un informe sobre el progreso del proyecto, con los desafíos y las estrategias que usamos para superarlos."},
                 "French": {"text": "Je dois soumettre un rapport sur l’avancement du projet, avec les défis rencontrés et les solutions mises en œuvre."},
                 "German": {"text": "Ich muss einen Bericht über den Fortschritt des Projekts vorlegen, der die Herausforderungen und die angewandten Lösungen enthält."},
                 "Chinese": {"text": "我需要提交一份关于项目进展的全面报告，包括遇到的挑战和为克服这些挑战而实施的策略。"},
                 "Arabic": {"text": "يجب عليّ تقديم تقرير عن تقدم المشروع، مع ذكر التحديات والحلول المستخدمة."},
                 "Italian": {"text": "Devo presentare una relazione sullo stato di avanzamento del progetto, con le sfide affrontate e le soluzioni adottate."},
                 "Russian": {"text": "Мне нужно представить подробный отчет о ходе проекта, включая встреченные трудности и примененные стратегии для их преодоления."},
                 "Japanese": {"text": "プロジェクトの進捗状況についての包括的な報告書を提出する必要があります。これには、直面した課題とそれを克服するために実施した戦略が含まれます。"},
                 "Portuguese": {"text": "Preciso enviar um relatório abrangente sobre o progresso do projeto, incluindo os desafios enfrentados e as estratégias implementadas para superá-los."},
                 "Czech": {"text": "Potřebuji předložit komplexní zprávu o pokroku projektu, včetně výzev, kterým čelím, a strategií implementovaných k jejich překonání."}}

    originalText = languages[originalLang]["text"]
    translatedText =  languages[targetLang]["text"]
    try:
        res = client.chat.completions.create(
            model="tiiuae/falcon-180B-chat",
            max_tokens=512,
            messages=[
                {"role": "system", "content": "You are a translator fluent in the following languages: English, Hindi, Spanish, French, German, Chinese, Arabic Italian, Russian, Japanese, Czech, and Portuguese. Translate the given text into simple words that are easy to understand in an explanation style. Keep your responses as short as possible."},
                {"role": "user", "content": f"Translate to {targetLang}: '{originalText}'"},
                {"role": "assistant", "content": translatedText},
                {"role": "user", "content": f"Translate to {targetLang}: '{text}'"},
            ],
        ).json()
    except Exception as e:
        print(e)
        return False
    except:
        return False

    translation = json.loads(res)['choices'][0]['message']['content']
    translation = translation.lstrip()
    translation = re.sub(r' \(.*?\)', '', translation)
    translation = re.sub(r'\nUser:', '', translation)
    return translation

def getTranslatedTranscript(segments, originalLang, targetLang):

    translated_segments = []
    for segment in segments:
        translated_text = falconTranslate(segment['text'], originalLang, targetLang)
        translated_segments.append({
            'text': translated_text,
            'start': segment['start'],
            'duration': segment['duration']
        })
    return translated_segments

def agetVoiceover(text, targetL, voiceID, file_path, speed=1.1):
    print(os.getcwd())
    client = texttospeech.TextToSpeechClient.from_service_account_json('./vigilant-shift-387520-8b24c9f46e78.json')

    voiceID = 'male' if voiceID == 1 else 'female'

    languages = {'Hindi': {'language_code': 'hi-IN', 'male': 'hi-IN-Wavenet-B', 'female': 'hi-IN-Wavenet-A'},
                 'English': {'language_code': 'en-US', 'male': 'en-US-Wavenet-A', 'female': 'en-US-Wavenet-C'},
                 'Spanish': {'language_code': 'es-ES', 'male': 'es-ES-Wavenet-B', 'female': 'es-ES-Wavenet-A'},
                 'French': {'language_code': 'fr-FR', 'male': 'fr-FR-Wavenet-B', 'female': 'fr-FR-Wavenet-A'},
                 'German': {'language_code': 'de-DE', 'male': 'de-DE-Wavenet-B', 'female': 'de-DE-Wavenet-A'},
                 'Chinese': {'language_code': 'hi-IN', 'male': 'cmn-CN-Wavenet-B', 'female': 'cmn-CN-Wavenet-A'},
                 'Arabic': {'language_code': 'ar-XA', 'male': 'ar-XA-Wavenet-B', 'female': 'ar-XA-Wavenet-A'},
                 'Italian': {'language_code': 'it-IT', 'male': 'it-IT-Wavenet-C', 'female': 'it-IT-Wavenet-A'},
                 'Russian': {'language_code': 'ru-RU', 'male': 'ru-RU-Wavenet-B', 'female': 'ru-RU-Wavenet-A'},
                 'Japanese': {'language_code': 'ja-JP', 'male': 'ja-JP-Wavenet-C', 'female': 'ja-JP-Wavenet-A'},
                 'Portuguese': {'language_code': 'pt-BR', 'male': 'pt-BR-Wavenet-B', 'female': 'pt-BR-Wavenet-A'},
                 'Czech': {'language_code': 'ko-KR', 'male': 'ko-KR-Wavenet-C', 'female': 'ko-KR-Wavenet-A'}}

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=speed
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code=languages[targetL]['language_code'],
        name=languages[targetL][voiceID]
    )

    synthesis_input = texttospeech.SynthesisInput(text=text)
    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
    except InvalidArgument as e:
        print(f"Invalid argument error: {e}")
        return False
    except PermissionDenied as e:
        print(f"Permission denied error: {e}")
        return False
    except Unauthenticated as e:
        print(f"Unauthenticated error: {e}")
        return False
    except GoogleAPIError as e:
        print(f"Google API error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    with open(file_path, 'wb') as outfile:
        outfile.write(response.audio_content)
    return True

def getVoiceover(a, b, c, d):
    client = texttospeech.TextToSpeechClient.from_service_account_json('vigilant-shift-387520-8b24c9f46e78.json')
    print('Got JSON')
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=1.0
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code='hi-IN',
        name='hi-IN-Wavenet-B'
    )
    print('Settings Done')
    
    print('Synthesizing...')
    synthesis_input = texttospeech.SynthesisInput(text='Hi how are you')
    print('Synthesized')


    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    print('Responded')

    with open('this_is_a_test_audio.mp3', 'wb') as outfile:
        outfile.write(response.audio_content)

def adjustAudioSpeed(audio_path, target_duration, text, targetL, voiceID):
    audio = AudioSegment.from_file(audio_path)
    current_duration = len(audio) / 1000  # Convert to seconds
    #print(current_duration, target_duration, f'Speed: {round(current_duration / target_duration, 2)}')

    speed_change = current_duration / target_duration
    #if speed_change <= 0.9:
    #    speed_change = 0.9
    #    adjusted_audio = audio.speedup(playback_speed=speed_change)
    #    adjusted_audio.export(audio_path, format="mp3")

    if speed_change > 1:
        getVoiceover(text, targetL, voiceID, audio_path, speed=speed_change)
    elif speed_change <= 0.9:
        getVoiceover(text, targetL, voiceID, audio_path, speed=0.9)



def writeNotes(groupedSentences, targetLang):
    languages = {'Arabic': 'ar', 'Chinese': 'zh-CN', 'English': 'en', 'French': 'fr',
                 'German': 'de', 'Hindi': 'hi', 'Japanese': 'ja', 'Portuguese': 'pt',
                 'Russian': 'ru', 'Spanish': 'es', 'Italian': 'it', 'Czech': 'cs'}

    notes = ""
    sentences = [entry['text'] for entry in groupedSentences]

    systemPrompt = "Please turn the following YouTube video transcription into easy-to-read notes. Summarize the content and format it in HTML. Make the notes simple and clear by: 1. Summarizing: Capture the main ideas and key points. 2. Simplifying: Use simple language and don't use first person perspective. 3. Highlighting: Emphasize important points. 4. Formatting: - Use bullet points for details and # for titles. - Create subheadings for different sections. - Make sure the notes are well-organized and easy to follow. Output the notes in the following format: ## Subheading - Bullet Point 1 - Bullet Point 2 - Bullet Point 3"
    userPrompt = "Please summarize the following part of the transcription of a video into clear, concise notes. Format the notes using HTML markdown, with well-organized subheadings (#) and bullet points (-). Make sure to use bullet points (-) and titles (#). Do not include Introduction or Conclusion as subheading, only topic related subheadings."

    chunk_size = 5
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i + chunk_size]
        messages = [{"role": "system", "content": systemPrompt}, {"role": "user", "content": (" ".join(chunk))+"\n"+userPrompt}]


        res = (client.chat.completions.create(
            model="tiiuae/falcon-180B-chat",
            messages=messages)
        ).json()

        res = json.loads(res)['choices'][0]['message']['content']
        res = res.lstrip()
        res = re.sub(r'\nUser:', '', res)

        translateNotes = GoogleTranslator(source="auto", target=languages[targetLang]).translate(res)
        notes += translateNotes

    return notes

def askQnA(groupedSentences, messageHistory, userQn):
    # messageHistory - History of Messages you've saved. Make sure to save it in {} with role, user/assistant, content
    # userQn - Question user asked at the end
    sentences = [entry['text'] for entry in groupedSentences]

    systemPrompt = """You will be provided with a large text. Your task is to thoroughly read and understand the text, ensuring you grasp its main ideas, details, and context. Afterward, you will answer questions related to the text. When answering questions, ensure your responses are:

Accurate: Provide precise and correct information based on the text.
Concise: Keep your answers brief and to the point, without unnecessary elaboration.
Contextual: Ensure your responses are relevant to the context of the text and the questions asked.
Here is the large text:"""
    messages = [{"role": "system", "content": systemPrompt}]    # Default System Prompt for QnA

    # Adding all the Transcribe to Messages
    chunk_size = 5
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i + chunk_size]
        #messages.append({"role": "user", "content": " ".join(chunk)})
        messages[0]['content'] += " ".join(chunk)

    # Add stored message history
    #messages.extend(messageHistory)
    messages.append({"role": "user", "content": userQn})

    res = (client.chat.completions.create(
        model="tiiuae/falcon-180B-chat",
        messages=messages)
    ).json()

    response = json.loads(res)['choices'][0]['message']['content']
    response = response.lstrip()
    response = re.sub(r'\nUser:', '', response)
    return response

def quizMCQ(groupedSentences, targetLang):
    sentences = [entry['text'] for entry in groupedSentences]  # Content of the Transcribe
    print(sentences)

    systemPrompt = """Given a detailed text content, generate a high-quality multiple-choice question (MCQ) to assess understanding of key information from the passage.

Steps to Follow:

Analyze the Text: Thoroughly read the provided text to comprehend the main ideas and important information.

Formulate the Question: Create a clear and concise question that directly relates to significant information in the text. The question should test comprehension of key concepts rather than trivial details.

Generate Options: Provide exactly four answer choices labeled A, B, C, and D. Ensure that one option is unambiguously correct based on the text, while the other three are plausible distractors but clearly incorrect according to the text.

Determine the Correct Answer: Identify which option is correct and ensure it is based on the text content.

Provide Explanation: Write a detailed explanation justifying why the correct answer is right and why the other options are incorrect, citing relevant parts of the text.

Output Format:

Present the MCQ in the following JSON structure:

```
{
  "question": "<Your question here>",
  "options": [
    "A. <First option>",
    "B. <Second option>",
    "C. <Third option>",
    "D. <Fourth option>"
  ],
  "correct_answer": "<Correct Option Letter (A/B/C/D)>",
  "explanation": "<Detailed explanation of why the correct answer is right and why other options are incorrect, citing relevant parts of the text.>"
}

```

Additional Guidelines:

**Focus on Key Concepts**: Ensure the question tests understanding of important concepts from the text.
**Clarity and Accuracy**: The question and all options must be grammatically correct and free of spelling errors.
**Plausible Distractors**: The distractors should be plausible to someone who hasn't fully understood the text but incorrect based on the text.
**Explanation Detail**: Provide a thorough explanation referencing specific parts of the text to justify the correct answer and explain why other options are incorrect.
**Options Lettering**: Options should strictly start with A/B/C/D 

Example Process:

**Analyze the Text**: Identify significant themes or topics.
**Formulate the Question**: Create a clear and concise question.
**Generate Options**: Provide four answer choices.
**Determine the Correct Answer**: Ensure one option is correct.
**Provide Explanation**: Write a detailed explanation.

The final JSON structure should be:


{
  "question": "<Your question here>",
  "options": [
    "A. <First option>",
    "B. <Second option>",
    "C. <Third option>",
    "D. <Fourth option>"
  ],
  "correct_answer": "<Correct Option Letter (A/B/C/D)>",
  "explanation": "<Detailed explanation of why the correct answer is right and why other options are incorrect, citing relevant parts of the text.>"
}

This format ensures that the MCQ task prompt is clear, structured, and follows a logical process similar to the provided example.

The text Content:\n

"""
    messages = [{"role": "system", "content": systemPrompt}]
    
    #messages.extend(example)
    # Adding all the Transcribe to Messages and the User's Question at the end as userQn
    chunk_size = 5
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i + chunk_size]
        messages[0]['content']+= " ".join(chunk)
        #messages.append({"role": "user", "content": " ".join(chunk)})
    #messages[0]['content']+="```"
    messages.append({"role": "user",
                "content": f"Generate a MCQ question with 4 options, provide the answer and solution in JSON. Keep the JSON keys and options 1, 2, 3, 4 in English and the Langauge: {targetLang}."})

    res = (client.chat.completions.create(
        model="tiiuae/falcon-180B-chat", temperature=0.3,
        messages=messages)
    ).json()

    response = json.loads(res)['choices'][0]['message']['content']
    response = response.lstrip()
    response = re.sub(r'\nUser:', '', response)
    return response



def _getVoiceOver(videoID, translatedTranscript, originalLang, targetLanguage, voiceID=1):
    
    combined_audio = AudioSegment.silent(duration=0)
    print("in voiceover (translated Transcript): ", translatedTranscript)
    for segment in translatedTranscript:
        text = segment['text']
        start_time = segment['start'] * 1000  # Convert to milliseconds
        duration = segment['duration']

        temp_audio_path = f".\\static\\audio\\{videoID}_temp_audio.mp3"
        try:
            status = getVoiceover(text, targetLanguage, voiceID, temp_audio_path)
            if not status:
                return False
        except Exception as e:
            print("Error in GetVoiceover", e)
            return False
        try:
            adjustAudioSpeed(temp_audio_path, duration, text, targetLanguage, voiceID)
        except Exception as e:
            print("Error in adjustAudioSpeed", e)
            return False
        try:
            audio_segment = AudioSegment.from_file(temp_audio_path)

            silence_before = AudioSegment.silent(duration=start_time - len(combined_audio))
        except Exception as e:
            print("Error AudioSegment:", e)
            return False
        except:
            import sys
            print("Unexpected Error:", sys.exc_info()[0], str(sys.exc_info()[2]))
        
        combined_audio += silence_before + audio_segment
    voiceover_dir = f".\\static\\audio\\{videoID}_voiceover.mp3"
    combined_audio.export(voiceover_dir, format="mp3")

