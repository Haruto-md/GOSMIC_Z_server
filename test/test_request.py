import requests
from scipy.io.wavfile import write
import numpy as np

url = 'http://localhost:8000/myapp/models/TTS/'  # TTSエンドポイントのURL

input_text = "やったぜ！！これでおさらばやわ。"
speaker_id = 42

data = {
    "input_text": input_text,
    "speaker_id":speaker_id
}

response = requests.post(url, data=data)

json_response = response.json()
audio_data = np.array(json_response["audio_data"]).astype(np.float32)

write("test/returned_audiofile.wav",json_response["sampling_rate"],audio_data)