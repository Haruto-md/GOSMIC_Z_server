#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import torch.cuda as cd
from vits.infer import AudioInferencer
from faster_whisper import WhisperModel

device = "cuda" if cd.is_available() else "cpu"
#modelをロード
audioInferer = AudioInferencer("pretrained_models\G_4000_42_Einstein.pth")
whisper_model = WhisperModel("medium",download_root="pretrained_models",compute_type="int8",device=device)
print("model loaded")
print("cuda available? -> "+device)
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GOSMIC_Z_server.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()