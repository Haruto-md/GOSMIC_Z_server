from django.urls import path
from .views import TTSView

urlpatterns = [
    path('models/TTS/', TTSView.as_view(), name='tts'),
    # 他のURLパターンを追加することもできます
]
