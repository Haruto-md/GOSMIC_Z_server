from django.urls import path
from .views import *

urlpatterns = [
    path('models/Whisper_ChatGPT_TTS/', Whisper_ChatGPT_TTS.as_view(), name='whisper_chatgpt_tts'),
    path('models/SpeechToText/', Whisper_ChatGPT_TTS.as_view(), name='SpeechToText'),
    path('models/Chat/', Whisper_ChatGPT_TTS.as_view(), name='Chat'),
    path('models/TextToSpeech/', Whisper_ChatGPT_TTS.as_view(), name='TextToSpeech'),
]
