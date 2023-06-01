from .modules.vits.infer import infer_audio
from django.http import JsonResponse
from rest_framework.views import APIView

# 他の必要なモジュールをインポートすることもできます

class TTSView(APIView):
    def post(self, request, format=None):
        input_text = request.data.get('input_text')
        speaker_id = request.data.get('speaker_id')

        # 必要な場合、model_pathの存在をチェックします
        if speaker_id:
            # model_pathが指定されている場合の処理
            speaker_id = int(speaker_id)
            audio_data, sampling_rate = infer_audio(input_text, speaker_id)
        else:
            # model_pathが指定されていない場合の処理
            audio_data, sampling_rate = infer_audio(input_text,42)

        return JsonResponse({'audio_data': audio_data.tolist(),"sampling_rate":sampling_rate})