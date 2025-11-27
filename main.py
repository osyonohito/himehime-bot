import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# ▼ 追加箇所ここから ▼
from dotenv import load_dotenv

# .envファイルがあれば読み込む（ローカル開発用）
# Cloud Run上では.envが無いので無視される（環境変数が使われる）
load_dotenv()

app = FastAPI()

# 環境変数からDiscordの公開鍵を取得（後で設定します）
# Cloud Runの環境変数設定で "DISCORD_PUBLIC_KEY" を入れます
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

@app.post("/")
async def interactions(request: Request):
    # 1. Discordからのリクエストかどうかの署名検証（必須セキュリティ）
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = await request.body()

    if not DISCORD_PUBLIC_KEY:
        return JSONResponse({"error": "No Public Key set"}, status_code=500)

    verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
    
    try:
        verify_key.verify(f"{timestamp}{body.decode()}".encode(), bytes.fromhex(signature))
    except BadSignatureError:
        raise HTTPException(status_code=401, detail="Invalid request signature")

    # 2. リクエストの中身を確認
    data = json.loads(body)
    
    # Type 1: Ping (DiscordがURL確認のために送ってくる)
    if data["type"] == 1:
        return JSONResponse({"type": 1})

    # Type 2: Slash Command (ユーザーが話しかけた時)
    if data["type"] == 2:
        # ここにキャラクターの返答ロジックを書きます
        # 今はとりあえず固定メッセージを返します
        user_input = data.get("data", {}).get("options", [])[0].get("value") if data.get("data", {}).get("options") else ""
        
        return JSONResponse({
            "type": 4, # 即時返信タイプ
            "data": {
                "content": f"あなたの言ったこと: {user_input} (これからここにAIを組み込みます！)"
            }
        })

    return JSONResponse({"error": "Unknown type"}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    # Cloud Runはポート8080をデフォルトで期待します
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))