import numpy as np
import scipy.io.wavfile as wf
from django.http import StreamingHttpResponse
from django.http.multipartparser import MultiPartParser
from rest_framework.views import APIView
import openai
import dotenv
import os
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.debug = False

END_binary_code="aaaabbbb".encode("utf-8")
AS_delimiter_binary="bbbbaaaa".encode("utf-8")

#modelをロード
from manage import audioInferer,whisper_model

class Whisper_ChatGPT_TTS(APIView):
    def post(self, request, format=None):
        def response_generator():
            parser = MultiPartParser(request.META, request, request.upload_handlers)
            # フォームデータの処理
            post, files = parser.parse()
            chat_data = []
            i=0
            for key, value in post.items():
                if "role" in key:
                    chat_data.append({"role":str(value)})
                elif "content" in key:
                    chat_data[-1]["content"] = str(value)
                    i+=1
                elif key=="sampling_rate":
                    sampling_rate = int(value)

            # ファイルの処理
            for key, uploaded_file in files.items():
                if key=="audio_data":
                    audio_binary_data = uploaded_file.read()
            audio_data =np.frombuffer(audio_binary_data,dtype=np.float32)
            print("chat_data",chat_data)
            print("audio_data:", audio_data)
            print("sampling_rate:", sampling_rate)
            wf.write("test/temp.wav" ,rate = sampling_rate,data = audio_data)

            # 同期処理
            # 音声データを文字起こしする
            transcription = self.whisper_transcribe(audio_data)
            print("transcription:",transcription)
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
            
            def getSentenceOfOpenAIStream(chat_data:dict,transcription:str):

                response_stream = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    messages= chat_data + [{"role": "user", "content": transcription}],
                    stream=True
                )
                acumulatedResponse = ""
                for item in response_stream:
                    choice = item['choices'][0]
                    if choice["finish_reason"] == "stop":
                        print("stop successfully.")
                        break
                    if choice["finish_reason"] == "length":
                        print("tokens expired")
                        break
                    if not "role" in choice["delta"].keys():
                        acumulatedResponse += choice["delta"]["content"]
                    if "。" in acumulatedResponse or "、" in acumulatedResponse:
                        yield acumulatedResponse
                        acumulatedResponse=""
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
            for slicedResponse in getSentenceOfOpenAIStream(chat_data=chat_data,transcription=transcription):
                print(slicedResponse)
                response_text = slicedResponse
                response_audio_data, sampling_rate = audioInferer.infer_audio(response_text,42)
                print("yielding response slice")
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