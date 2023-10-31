import numpy as np
import scipy.io.wavfile as wf
import time
from django.http import StreamingHttpResponse,HttpResponse
from django.http.multipartparser import MultiPartParser
from rest_framework.views import APIView
import json
import openai
import dotenv
import os
import glob
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.debug = False

import torch
from vits.infer import AudioInferencer
from faster_whisper import WhisperModel

device = "cuda" if torch.cuda.is_available() else "cpu"
#modelをロード
whisper_model = WhisperModel("medium",download_root="pretrained_models",compute_type="int8",device=device)
audioInferer = AudioInferencer("pretrained_models\ChaCha_G_1000.pth",device=device)
# audioInferer = AudioInferencer("pretrained_models\G_4000_42_Einstein.pth")
text = "はじめまして！ボクの名前はチャメーバだよー"
audio_data, sampling_rate = audioInferer.infer_audio(text,11)
print("model loaded")
print("cuda available? -> "+device)

def whisper_transcribe(audioPath):
    segments, info = whisper_model.transcribe(audio=audioPath, language="ja", beam_size=3,temperature=0.2)
    transcription = " ".join([seg.text  for seg in segments])
    return transcription

class SpeechToText(APIView):
    def post(self,request,format=None):
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        # フォームデータの処理
        post, files = parser.parse()
        i=0
        for key, value in post.items():
            if key=="sampling_rate":
                sampling_rate = int(value)
            else:
                print("[ERROR] else.")

        # ファイルの処理
        for key, uploaded_file in files.items():
            if key=="audio_data":
                audio_binary_data = uploaded_file.read()
        audio_data =np.frombuffer(audio_binary_data,dtype=np.float32)
        wf.write("tempFiles/temp.wav" ,rate = sampling_rate,data = audio_data)

        # 音声データを文字起こしする
        transcription = self.whisper_transcribe("tempFiles/temp.wav")
        print("transcription:",transcription)
        # JSONレスポンスを作成
        response_data = {"transcription": transcription}
        # JSONレスポンスを返す
        return HttpResponse(json.loads(response_data))

class Chat(APIView):
    def post(self, request, format=None):
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        # フォームデータの処理
        post, files = parser.parse()
        chat_data = []
        for key, value in post.items():
            if "role" in key:
                chat_data.append({"role": str(value)})
            elif "content" in key:
                chat_data[-1]["content"] = str(value)
            elif "prompt" in key:
                prompt = value
            elif "temp_token" in key:
                temp_token = value
            else:
                print("[ERROR] else.")

        # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る処理をそのまま含める
        response_stream = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=chat_data + [{"role": "user", "content": prompt}],
            stream=True
        )
        
        acumulatedResponse = ""
        os.mkdir(f"./tempFiles/chat/{temp_token}")
        resulting_sentences = []
        for item in response_stream:
            choice = item['choices'][0]
            if choice["finish_reason"] is None:
                if not "role" in choice["delta"].keys():
                    acumulatedResponse += choice["delta"]["content"].replace("「", "").replace("」", "")
                if "。" in acumulatedResponse or "、" in acumulatedResponse:
                    resulting_sentences.append(acumulatedResponse)
                    with open(f"./tempFiles/chat/{temp_token}/{len(resulting_sentences)}","w",encoding="utf-8") as f:
                        temp_json_dict = {
                            "response":acumulatedResponse,
                            "response_index":len(resulting_sentences)
                        }
                        temp_json_data = json.loads(temp_json_dict)
                        f.write(temp_json_data)
                    acumulatedResponse = ""
            else:
                print("[Info] Finished Chatting ,for" + choice["finish_reason"])
                response_data = json.loads({
                    "finish_reason":choice["finish_reason"],
                    "resulting_sentences":" ".join(resulting_sentences)
                })

        return HttpResponse(response_data,type="text/json")

class ChatGetNew(APIView):
    def post(self,request,format=None):
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        # フォームデータの処理
        post, files = parser.parse()
        for key, value in post.items():
            if key=="temp_token":
                temp_token = value
            else:
                print("[ERROR] else.")
        
        response_josn = {
            "state":"",
            "content":{
                "response":"",
                "response_index":0    
                }
            }
        
        if not os.path.exists(f"./tempFiles/chat/{temp_token}"):
            response_josn["state"] = "Failed"
            response_josn["content"] = "No such token"
            return HttpResponse(json.loads(response_josn),type="text/json")
        files = glob.glob(f"./tempFiles/chat/{temp_token}/*")
        if len(files) == 0:
            response_josn["state"] = "Wait"
            response_josn["content"] = "Chat not saved yet."
            return HttpResponse(json.loads(response_josn),type="text/json")
        newFile = files[0]
        with open(newFile,"r",encoding="utf-8") as f:
            chat_delta_json = f.read()
        os.remove(newFile)
        response_josn["state"] = "Success"
        response_josn["content"] = chat_delta_json
        return HttpResponse(json.loads(response_josn),type="text/json")

class TextToSpeech(APIView):
    def post(self,request,format=None):
        parser = MultiPartParser(request.META, request, request.upload_handlers)
        # フォームデータの処理
        post, files = parser.parse()
        for key, value in post.items():
            if key=="text":
                text = str(value)
            else:
                print("[ERROR] else.")
        print(f"generate audio file :'{text}'")
        response_audio_data, _ = audioInferer.infer_audio(text,42)
        response_audio_byte_data = response_audio_data.tobytes()
        return HttpResponse(response_audio_byte_data,type="application/octet-stream")

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
                else:
                    print("[ERROR] else.")

            # ファイルの処理
            for key, uploaded_file in files.items():
                if key=="audio_data":
                    audio_binary_data = uploaded_file.read()
            audio_data =np.frombuffer(audio_binary_data,dtype=np.float32)
            wf.write("tempFiles/temp.wav" ,rate = sampling_rate,data = audio_data)

            # 音声データを文字起こしする
            transcription = self.whisper_transcribe("tempFiles/temp.wav")
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る

            def getSentenceOfOpenAIStream(chat_data:dict,transcription:str):

                response_stream = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    messages= chat_data + [{"role": "user", "content": transcription}],
                    stream=True
                )
                print("transcription:",transcription)
                acumulatedResponse = ""
                for item in response_stream:
                    choice = item['choices'][0]
                    if choice["finish_reason"] is None:
                        if not "role" in choice["delta"].keys():
                            acumulatedResponse += choice["delta"]["content"].replace("「","").replace("」","")
                        if "。" in acumulatedResponse or "、" in acumulatedResponse:
                            yield acumulatedResponse
                            acumulatedResponse=""
                    else:
                        print(choice["finish_reason"])
            # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る
            for slicedResponse in getSentenceOfOpenAIStream(chat_data=chat_data,transcription=transcription):
                print(slicedResponse)
                response_text = slicedResponse
                response_audio_data, _ = audioInferer.infer_audio(response_text,5)
                print("yielding response slice")
                yielding_component = response_audio_data.tobytes()
                yield yielding_component

        response = StreamingHttpResponse(response_generator(), content_type='application/octet-stream')
        return response

    def whisper_transcribe(self, audioPath):
        segments, info = whisper_model.transcribe(audio=audioPath, language="ja", beam_size=3,temperature=0.2)
        transcription = " ".join([seg.text  for seg in segments])
        return transcription

    async def awaitAudioInfer(self,response_text):
        return await audioInferer.infer_audio(response_text)

    def text_cleaner_for_audioInferer(text):
        banned_chars = [".","…"]
        for banned_char in banned_chars:
            text.replace(banned_char,"")
        return text
