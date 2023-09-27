# runserver_ssl.py

import os
from django.core.management.commands import runsslserver
from decouple import config

class Command(runsslserver.Command):
    def handle(self, *args, **options):
        # .env ファイルから証明書と秘密鍵ファイルのパスを読み取ります
        certificate_path = config('SSL_CERTIFICATE_PATH', default=None)
        private_key_path = config('SSL_PRIVATE_KEY_PATH', default=None)
        private_key_password = config('SSL_PRIVATE_KEY_PASSWORD', default=None)

        if not certificate_path or not private_key_path:
            raise ValueError("SSL_CERTIFICATE_PATH and SSL_PRIVATE_KEY_PATH must be defined in the .env file.")

        # runsslserver コマンドのオプションを設定します
        # options['addr'] = '0.0.0.0'
        # options['port'] = 443
        options['certfile'] = certificate_path
        options['keyfile'] = private_key_path
        # options['ssl_version'] = 'TLSv1_2'  # 必要に応じてSSLバージョンを指定してください

        if private_key_password:
            options['key-password'] = private_key_password

        super().handle(*args, **options)