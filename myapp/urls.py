from django.urls import path
from .views import *

urlpatterns = [
    path('models/TTS/', TTSView.as_view(), name='tts'),
    # 他のURLパターンを追加することもできます
    path('models/Whisper_ChatGPT_TTS/', Whisper_ChatGPT_TTS.as_view(), name='whisper_chatgpt_tts'),
]
