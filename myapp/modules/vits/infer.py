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
def infer_audio(text,speaker_id):
    hps = utils.get_hparams_from_file("myapp\modules\\vits\configs\config_Einstein.json")
    net_g = SynthesizerTrn(
        len(symbols),
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model)
    _ = net_g.eval()

    _ = utils.load_checkpoint("myapp\modules\vits\pretrained_model\G_4000_42_Einstein.pth", net_g, None)
    stn_tst = get_text(text, hps)
    with torch.no_grad():
        x_tst = stn_tst.unsqueeze(0)
        x_tst_lengths = torch.LongTensor([stn_tst.size(0)])
        sid = torch.LongTensor([speaker_id])
        audio = net_g.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667, noise_scale_w=0.8, length_scale=0.8)[0][0,0].data.cpu().float().numpy()
        sampling_rate = hps.data.sampling_rate
    return (audio,sampling_rate)