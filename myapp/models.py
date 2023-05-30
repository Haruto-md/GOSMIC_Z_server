from django.db import models

class Speech(models.Model):
    audio_file = models.FileField(upload_to='audio/')
    # 他の必要なフィールドを追加することもできます