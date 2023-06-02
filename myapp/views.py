from io import BytesIO
import wave
from vits.infer import AudioInferencer
from django.http import StreamingHttpResponse,JsonResponse
from rest_framework.views import APIView

from faster_whisper import WhisperModel
import openai
import dotenv
import os
dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

#modelをロード
audioInferer = AudioInferencer("pretrained_models\G_4000_42_Einstein.pth")
whisper_model = WhisperModel("small",download_root="pretrained_models",compute_type="int8")


class TTSView(APIView):
    def post(self, request, format=None):
        input_text = request.data.get('input_text')
        speaker_id = request.data.get('speaker_id')

        # 必要な場合、model_pathの存在をチェックします
        if speaker_id:
            # model_pathが指定されている場合の処理
            speaker_id = int(speaker_id)
            audio_data, sampling_rate = audioInferer.infer_audio(input_text, speaker_id)
        else:
            # model_pathが指定されていない場合の処理
            audio_data, sampling_rate = audioInferer.infer_audio(input_text,42)

        return JsonResponse({"audio_data":audio_data.tolist(),"sampling_rate":sampling_rate})


class Whisper_ChatGPT_TTS(APIView):
    async def post(self, request, format=None):
        # 音声データをストリーミングで受け取る
        audio_data = b""
        async for chunk in request.stream():
            audio_data += chunk

        # 音声データを文字起こしする
        transcription = self.whisper_transcribe(audio_data)

        # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
        async with self.openai_request(transcription) as response_stream:
            response_text = await self.read_stream_response(response_stream)

        # GPT-3.5 Turboのレスポンスを使って音声データを生成する
        response_audio_data, sampling_rate = await self.stream_infer_audio(response_text)


        # 音声データをwav形式で保存する
        output_audio = BytesIO()
        with wave.open(output_audio, 'wb') as wav_file:
            wav_file.setnchannels(1)  # モノラル
            wav_file.setsampwidth(2)  # 16ビット
            wav_file.setframerate(sampling_rate)
            wav_file.writeframes(response_audio_data.tobytes())

        # 音声データをストリーミングレスポンスとして返す
        response = StreamingHttpResponse(output_audio.getvalue(), content_type='audio/wav')
        response['Content-Disposition'] = 'attachment; filename="audio.wav"'
        return response

    def whisper_transcribe(audioData):
        segments, info = whisper_model.transcribe(audioData, language="ja", beam_size=5)
        transcription = " ".join([seg.text  for seg in segments])
        return transcription
    
    async def openai_request(self, text,chat_data):
        # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る処理を実装する
        # このメソッドは非同期でレスポンスを返す

        # 仮の実装: ダミーレスポンスストリームを返す
        response = openai.ChatCompletion.create(engine="gpt-3.5-turbo",
                                    temperature=0.7,
                                    max_tokens = 50,
                                    messages=chat_data.append({"role":"user","content":text}),
                                    stream = True
                                    )
        return response

    async def read_stream_response(self, response_stream):
        # ストリームレスポンスを受け取り、テキストデータを読み取る処理を実装する
        # このメソッドは非同期でレスポンステキストを返す

        # 仮の実装: レスポンスストリームを文字列に連結する
        response_text = " ".join(response_stream)
        return response_text

    async def stream_infer_audio(self, text):
        # テキストを音声データに変換する処理を実装する
        # このメソッドは非同期で音声データとサンプリングレートを返す
        
        audio_data, sampling_rate = audioInferer.infer_audio(text, speaker_id=42)
        return audio_data, sampling_rate

    def stream_audio_data(self, audio_data):
        # 音声データをストリームとして返すジェネレータ関数を実装する
        # このメソッドは音声データを一定のチャンクごとに返す

        # 仮の実装: 音声データをチャンクごとに返す
        chunk_size = 512
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i+chunk_size]