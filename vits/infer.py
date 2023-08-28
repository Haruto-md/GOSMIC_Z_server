import torch
from . import commons
from . import utils
from .models import SynthesizerTrn
from .text.symbols import symbols
from .text import text_to_sequence

def get_text(text, hps):
    text_norm = text_to_sequence(text, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = torch.LongTensor(text_norm)
    return text_norm

class AudioInferencer():
    def __init__(self,modelPath) -> None:
        self.modelPath = modelPath
        self.load_model(self.modelPath)
        
    def load_model(self,modelPath):
        self.hps = utils.get_hparams_from_file("pretrained_models\configs\config_Einstein.json")
        self.net_g = SynthesizerTrn(
            len(symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            n_speakers=self.hps.data.n_speakers,
            **self.hps.model)
        _ = self.net_g.eval()
        try:
            _ = utils.load_checkpoint(modelPath, self.net_g, None)
        except:
            print("[ERROR]model name is different. Can't load checkpoint.")
            
    def infer_audio(self,text,speaker_id=42):
        
        stn_tst = get_text(text, self.hps)
        with torch.no_grad():
            x_tst = stn_tst.unsqueeze(0)
            x_tst_lengths = torch.LongTensor([stn_tst.size(0)])
            sid = torch.LongTensor([speaker_id])
            audio = self.net_g.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667, noise_scale_w=0.8, length_scale=0.8)[0][0,0].data.cpu().float().numpy()
            sampling_rate = self.hps.data.sampling_rate
        return (audio,sampling_rate)