# Pythonの軽量イメージを使用
FROM python:3.9-slim

# 作業ディレクトリ設定
WORKDIR /app

# ライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# コードをコピー
COPY . .

# Cloud Runで動かすコマンド
CMD ["python", "main.py"]