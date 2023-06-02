
import requests
from scipy.io.wavfile import read,write
import numpy as np


url = 'http://localhost:8000/myapp/models/TTS/'  # TTSエンドポイントのURL

input_text = "こちらはサンプル音声ですじゃ。"
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
audio_data = audio_data.astype(np.float32) / 32767.0  # 音声データを正規化

data = {
    "audio_data": audio_data,
    "sampling_rate":sampling_rate,
    "chat_data":[{"role":"user","content":"""今から以下の情報を元にアリアンナとして会話してください。一つ一つのセリフは簡潔に、素っ気なさを感じさせるようにしてください。 
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
「魔法の力を使うことは、常に相手に対して優位に立つことを意味するわけではありません。」"""},
                 {"role":"user","content":"こんにちは。"}]
}


# リクエストを送信して音声データをストリーミングで受け取る
response = requests.post(url, data=data, stream=True)

# 音声データをストリーミングで保存する
output_audio_path = "test/returned_audiofile_v2.html"
with open(output_audio_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=512):
        f.write(chunk)

print("Saved as", output_audio_path)