import numpy as np
import scipy.io.wavfile as wf
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
print("model loaded")
print("cuda available? -> "+device)

def whisper_transcribe(audioPath):
    segments, info = whisper_model.transcribe(audio=audioPath, language="ja", beam_size=3,temperature=0.2)
    transcription = " ".join([seg.text  for seg in segments])
    return transcription
def text_cleaner_for_audioInferer(text):
    banned_chars = [".","…","。","：",":"]
    for banned_char in banned_chars:
        text.replace(banned_char," ")
    return text

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
        transcription = whisper_transcribe("tempFiles/temp.wav")
        print("transcription:",transcription)
        # JSONレスポンスを返す
        return HttpResponse(transcription)

class Chat(APIView):
    def post(self, request, format=None):
        chat_data = []
        for key, value in request.data.items():
            if "role" in key:
                chat_entry = {"role": str(value)}
            elif "content" in key:
                chat_entry["content"] = str(value)
                chat_data.append(chat_entry)
        temp_token = request.data.get("temp_token")

        # GPT-3.5 Turboにテキストを送信し、ストリームでレスポンスを受け取る処理をそのまま含める
        response_stream = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=chat_data,
            stream=True
        )
        # f"./tempFiles/chat/{temp_token} ToDo
        acumulatedResponse = ""
        os.mkdir(f"./tempFiles/chat/{temp_token}")
        resulting_sentences = []
        for item in response_stream:
            choice = item['choices'][0]
            if choice["finish_reason"] is None:
                if not "role" in choice["delta"].keys():
                    acumulatedResponse += choice["delta"]["content"].replace("「", "").replace("」", "").replace("\n", " ")
                if "。" in acumulatedResponse or "、" in acumulatedResponse:
                    print(f"[chat delta]{acumulatedResponse}")
                    resulting_sentences.append(acumulatedResponse)
                    with open(f"./tempFiles/chat/{temp_token}/{len(resulting_sentences)}","w",encoding="utf-8") as f:
                        temp_json_dict = {
                            "response":acumulatedResponse,
                            "response_index":len(resulting_sentences)
                        }
                        temp_json_data = json.dumps(temp_json_dict)
                        f.write(temp_json_data)
                    acumulatedResponse = ""
            else:
                with open(f"./tempFiles/chat/{temp_token}/{len(resulting_sentences)+1}","w",encoding="utf-8") as f:
                    temp_json_dict = {
                        "response":"END",
                        "response_index":-1
                    }
                    temp_json_data = json.dumps(temp_json_dict)
                    f.write(temp_json_data)
                print("[Info] Finished Chatting ,for " + choice["finish_reason"])
                response_data = json.dumps({
                    "finish_reason":choice["finish_reason"],
                    "resulting_sentences":" ".join(resulting_sentences)
                })

        return HttpResponse(response_data,content_type="text/json")

class GetNewChat(APIView):
    def post(self,request,format=None):
        temp_token = request.data.get("token")

        response_josn = {
            "state":"",
            "content":{
                "response":"",
                "response_index":0
                }
            }

        if not os.path.exists(f"./tempFiles/chat/{temp_token}"):
            response_josn["state"] = "Wait"
            response_josn["content"]["response"] = "No such token folder"
            return HttpResponse(json.dumps(response_josn),content_type="text/json")
        files = glob.glob(f"./tempFiles/chat/{temp_token}/*")
        sorted_files = sorted(files, key=lambda x: int(x.split("/")[-1].split("\\")[-1]))
        if len(sorted_files) == 0:
            response_josn["state"] = "Wait"
            response_josn["content"]["response"] = "Chat not saved yet."
            return HttpResponse(json.dumps(response_josn),content_type="text/json")
        newFile = sorted_files[0]
        with open(newFile,"r",encoding="utf-8") as f:
            chat_delta_json = f.read()
        os.remove(newFile)
        response_josn["state"] = "Success"
        response_josn["content"] = json.loads(chat_delta_json)
        return HttpResponse(json.dumps(response_josn),content_type="text/json")

class TextToSpeech(APIView):
    character_model_name = "Chameba"
    audioInferer = AudioInferencer(f"./pretrained_models/{character_model_name}.pth",device=device)
    def post(self,request,format=None):
        # フォームデータの処理
        text = request.data.get("text")
        character = request.data.get("character")
        if  character is not self.character_model_name:
            self.character_model_name = character
            self.audioInferer = AudioInferencer(f"./pretrained_models/{self.character_model_name}.pth",device=device)
        cleaned_text = text_cleaner_for_audioInferer(text)
        response_audio_data, sampling_rate = self.audioInferer.infer_audio(cleaned_text,42)
        response_audio_byte_data = response_audio_data.tobytes()
        return HttpResponse(response_audio_byte_data,content_type="application/octet-stream")

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
            transcription = whisper_transcribe("tempFiles/temp.wav")
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