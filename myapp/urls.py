from django.urls import path
from .views import *

urlpatterns = [
    path('models/Whisper_ChatGPT_TTS/', Whisper_ChatGPT_TTS.as_view(), name='whisper_chatgpt_tts'),
    path('models/SpeechToText/', SpeechToText.as_view(), name='SpeechToText'),
    path('models/Chat/', Chat.as_view(), name='Chat'),
    path('models/Chat/GetNewChat/', GetNewChat.as_view(), name='GetNewChat'),
    path('models/TextToSpeech/', TextToSpeech.as_view(), name='TextToSpeech'),
]
