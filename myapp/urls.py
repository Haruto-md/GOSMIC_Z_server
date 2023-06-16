from django.urls import path
from .views import *

urlpatterns = [
    path('models/Whisper_ChatGPT_TTS/', Whisper_ChatGPT_TTS.as_view(), name='whisper_chatgpt_tts'),
]
