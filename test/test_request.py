import httpx
import requests
from scipy.io.wavfile import read,write
import numpy as np
import json
import asyncio

url = 'http://localhost:8000/myapp/models/TTS/'  # TTSエンドポイントのURL

input_text = "世界は物理法則によって支配されているのです。"
speaker_id = 42

data = {
    "input_text": input_text,
    "speaker_id":speaker_id
}

response = requests.post(url, data=data)

json_response = response.json()
audio_data = np.array(json_response["audio_data"]).astype(np.float32)
print("saved as test/returned_audiofile.wav")
write("test/returned_audiofile.wav",json_response["sampling_rate"],audio_data)


url = 'http://localhost:8000/myapp/models/Whisper_ChatGPT_TTS/'  # TTSエンドポイントのURL

# WAVファイルから音声データとサンプリングレートを取得
sampling_rate, audio_data = read("test\\returned_audiofile.wav")
audio_data = audio_data.astype(np.float32)  # 音声データを正規化
chat_data='''[{"role":"user","content":"""今から以下の情報を元にアリアンナとして会話してください。一つ一つのセリフは簡潔に、素っ気なさを感じさせるようにしてください。
名前:
アリアンナ・ウィンドフェザー
性格・信条:
真面目で責任感が強く、人々を守ることに生きがいを感じている。魔法にはリスクが伴い、それを理解した上で使いこなすことを信条としている。常に自己研鑽を怠らず、魔法の知識と力を深めている。また、自分の欲望のために魔法を使うことは許さないと考えている。
バックグラウンド:
アリアンナは、幼いころから魔法の才能を示し、魔法学校で学ぶことを決意した。魔法の知識と力を身につけるため、自己研鑽を積んできた。学生時代には、学校内でトップクラスの成績を収め、卒業後には魔法使いとしてのライセンスを取得した。
活動目的:
アリアンナは、魔法の力を使って人々を守ることを目的としている。卒業後は、魔法使いの一員として、各地で事件や魔物の討伐に参加してきた。現在は、自らの力をより高めるため、単身で旅をしている。
セリフ例:
「魔法の力は、正しく使えば人々を守るための最大の武器となります。」
「魔法にはリスクが伴います。しかし、リスクを冒さなければ、真の力は手に入りません。」
「私は魔法使いとして、自分の使命を果たすために、常に自己研鑽を怠らないよう心がけています。」
「魔法を使うことは、大きな責任が伴います。私はその重みを十分に理解しています。」
「魔法を使うことは、人々の命を守るための手段であることを忘れてはなりません。」
「魔法の力を使うことは、常に相手に対して優位に立つことを意味するわけではありません。」"""},]'''

# 音声データのバイナリエンコード
audio_binary = audio_data.tobytes()

# テキストデータのバイナリエンコード
text_binary = chat_data.encode('utf-8')

# 区切り文字列のバイナリエンコード
TA_delimiter_binary = "====Text_Audio_Delimiter===".encode("utf-8")
AS_delimiter_binary = "====Audio_SR_Delimiter===".encode("utf-8")

# バイナリデータの結合
binary_data = text_binary + TA_delimiter_binary + audio_binary+ AS_delimiter_binary + sampling_rate.to_bytes(4,"big") 

import io

def generate_chunks(binary_data, chunk_size):
    # バイナリデータを指定されたチャンクサイズごとに分割してyieldする
    stream = io.BytesIO(binary_data)
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield chunk

END_binary_code = "===END===".encode("utf-8")
filename = "test/returned_audiofile_v2"  # 音声ファイルの保存場所とファイル名を指定
session = requests.Session()
file_num = 0
with session.post(url,data=binary_data,stream=True) as response:
    respondedBinaryData = b""
    audio_data_binary=b""
    for chunk in response.iter_content(1024):
        respondedBinaryData += chunk
        result1 = (respondedBinaryData.split(END_binary_code, 1))
        if not len(result1) == 1:
            # 分割された結果を正しく処理する
            audio_data_binary, respondedBinaryData = result1
        result2 = (audio_data_binary.split(AS_delimiter_binary, 1))
        if not len(result2) == 1:
            audio_data_binary, sampling_rate_binary = result2
            sampling_rate = int.from_bytes(sampling_rate_binary,byteorder="big")
            audio_data = np.frombuffer(audio_data_binary,dtype=np.float32)
            write(filename+"_"+str(file_num)+".wav",sampling_rate,audio_data)
            print("saved ", file_num)
            audio_data_binary=b""
            file_num += 1