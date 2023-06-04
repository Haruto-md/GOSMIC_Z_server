import numpy as np
import json
import scipy.io.wavfile as wf
from django.http import JsonResponse,StreamingHttpResponse
from rest_framework.views import APIView
import openai
import dotenv
import os
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.debug = False

#modelをロード
from manage import audioInferer,whisper_model

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
    def post(self, request, format=None):
        def response_generator():
            # 音声データをストリーミングで受け取る
            binary_data = b""
            print(request)
            for chunk in request.stream:
                binary_data += chunk
            # 区切り文字列のバイナリエンコード
            TA_delimiter_binary = "====Text_Audio_Delimiter===".encode("utf-8")
            AS_delimiter_binary = "====Audio_SR_Delimiter===".encode("utf-8")
            END_binary_code = "===END===".encode("utf-8")
            # データの分割
            text_binary, audio_binary = binary_data.split(TA_delimiter_binary, 1)
            audio_data_binary, sampling_rate = audio_binary.split(AS_delimiter_binary, 1)
            # 音声データの復元
            
            audio_data = np.frombuffer(audio_data_binary,dtype=np.float32)
            sampling_rate = int.from_bytes(sampling_rate,byteorder="big")
            # テキストデータの復元
            chat_data = json.loads(text_binary.decode('utf-8'))
            print("audio_data:", len(audio_data))
            print("sampling_rate:", sampling_rate)
            wf.write("temp.wav" ,rate = sampling_rate,data = audio_data)
            print(chat_data)

            # 同期処理
            # 音声データを文字起こしする
            transcription = self.whisper_transcribe(audio_data)
            print("transcription:",transcription)
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
            
            def getSentenceOfOpenAIStream(chat_data:dict,transcription:str):
            
                response_stream = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_tokens=100,
                    messages= chat_data + [{"role": "user", "content": transcription}],
                    stream=True
                )
                acumulatedResponse = ""
                for item in response_stream:
                    choice = item['choices'][0]
                    if choice["finish_reason"]=="stop":
                        break
                    if not "role" in choice["delta"].keys():
                        acumulatedResponse += choice["delta"]["content"]
                    if "。" in acumulatedResponse or "、" in acumulatedResponse:
                        yield acumulatedResponse
                        acumulatedResponse=""
            # 非同期?
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
            for slicedResponse in getSentenceOfOpenAIStream(chat_data=chat_data,transcription=transcription):
                print(slicedResponse)
                response_text = slicedResponse
                response_audio_data, sampling_rate = audioInferer.infer_audio(response_text,42)
                yield  response_audio_data.tobytes() + AS_delimiter_binary + sampling_rate.to_bytes(4,"big") + END_binary_code
                
        
        response = StreamingHttpResponse(response_generator(), content_type='audio/wav')
        response['Content-Disposition'] = 'attachment; filename="audio.wav"'
        return response

    def whisper_transcribe(self, audioData):
        segments, info = whisper_model.transcribe(audio=audioData, language="ja", beam_size=5)
        transcription = " ".join([seg.text  for seg in segments])
        return transcription
                
    async def awaitAudioInfer(self,response_text):
        return await audioInferer.infer_audio(response_text)
