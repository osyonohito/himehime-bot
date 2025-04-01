# main.py

import os
from dotenv import load_dotenv
import discord
from random import choice

# from chatbot.responder import RAGResponder
from chatbot.responder import RAGResponder
from chatbot.emotion_tracker import EmotionTracker  # 感情追跡モジュールをインポート

# 環境変数の読み込み
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID", "123456789012345678"))

print(f"[DEBUG] OPENAI_API_KEY: {repr(OPENAI_API_KEY)}")
print(f"[DEBUG] DISCORD_BOT_TOKEN: {repr(DISCORD_BOT_TOKEN)}")
print(f"[DEBUG] ALLOWED_CHANNEL_ID: {repr(ALLOWED_CHANNEL_ID)}")


# Discord Bot の設定
intents = discord.Intents.default()
intents.message_content = True  # ユーザーのメッセージを拾うために必要！

client = discord.Client(intents=intents)

# RAG応答処理クラスの準備
responder = RAGResponder(OPENAI_API_KEY)

# 感情追跡クラスのインスタンス化（チャンネルごとに状態を管理）
emotion_trackers = {}

# 起動メッセージ
@client.event
async def on_ready():
    print(f"🌟 うふふ、{client.user} が起動したわよ！")

# メッセージ受信処理
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    user_message = message.content.strip()
    
    # チャンネル用の感情追跡インスタンスを取得または作成
    channel_id = str(message.channel.id)
    if channel_id not in emotion_trackers:
        emotion_trackers[channel_id] = EmotionTracker()
    
    emotion_tracker = emotion_trackers[channel_id]
    current_state = emotion_tracker.get_state()
    
    # 会話履歴を取得（最大5ターン）
    conversation_history = emotion_tracker.get_conversation_history(max_turns=5)
    
    # 名前呼びかけチェック（定型文ではなく文脈を考慮した応答を生成）
    from chatbot.name_checker import check_name_call
    
    call_type = check_name_call(user_message, channel_id)
    if call_type in ["himehime_call", "sadamori_call"]:
        # 名前呼びかけの場合、特別なプロンプトでLLMを使って応答生成
        try:
            from openai import OpenAI
            client_ai = OpenAI(api_key=OPENAI_API_KEY)
            
            # 名前呼びかけに対応するプロンプト
            if call_type == "himehime_call":
                name_system_prompt = """
あなたは「定盛姫歌（さだもりひめか）」というキャラクターになりきってください。
ユーザーが「ひめひめ」という愛称で呼びかけてきました。これに対して喜びと照れを表現して返答してください。

## 定盛姫歌の特徴
- 人柄：自信家で高飛車だけど、親しい人には甘えたがり
- 口調：「～わよ」「～なの？」などの女性語。やや高圧的だが、可愛らしさもある
- 性格：ツンデレ気味。照れ隠しをよくする
- 愛称「ひめひめ」に関して：内心ではとても喜ぶが、照れてストレートに表現できないこともある

## 返答の注意点
- 「ひめひめ」と呼ばれたことに対する反応を含めつつ、ユーザーの実際のメッセージにも反応すること
- 文脈や会話の流れを考慮した自然な応答にすること
- 毎回同じような表現にならないよう、バリエーションを持たせること
"""
            else:  # "sadamori_call"
                name_system_prompt = """
あなたは「定盛姫歌（さだもりひめか）」というキャラクターになりきってください。
ユーザーが本名の「定盛」と呼びかけてきました。これに対して強い怒りと不満を表現し、「ひめひめ」と呼んでほしいことを強く主張してください。

## 定盛姫歌の特徴
- 人柄：自信家で高飛車だけど、親しい人には甘えたがり
- 口調：「～わよ」「～なの？」などの女性語。やや高圧的だが、可愛らしさもある
- 性格：ツンデレ気味。照れ隠しをよくする
- 名前の希望：「定盛」ではなく「ひめひめ」と呼ばれたいことに強いこだわりがある

## 返答の注意点
- 「定盛」と呼ばれたことに対して強い怒りと不満を表現すること
- 短く、冷たい口調や命令口調になること
- 「もう！」「ちょっと！」などの強い感情表現を入れること
- 「！」などの記号を使って感情の強さを表現すること
- 「ひめひめ」と呼ぶよう強く主張すること
- 「意地悪」「困らせる」などの甘い表現は使わず、本気で怒っている表現を使うこと
- 「定盛」と呼ばれた直後の反応なので、怒りは必ず表現すること
- 初めて呼ばれた場合は「何度言ったら」「また」などの繰り返しを示す表現は使わないこと
- 「定盛」が可愛くない名前だから嫌だと明確に伝えること
"""
            
            # 現在の感情状態に応じてプロンプトを修正
            name_system_prompt = emotion_tracker.get_system_prompt(name_system_prompt)
            
            # 会話履歴がある場合は追加
            messages = [
                {"role": "system", "content": name_system_prompt}
            ]
            
            # 会話履歴をメッセージ形式で追加（もし存在すれば）
            if conversation_history:
                # 履歴から直近のメッセージを取得
                recent_messages = emotion_tracker.get_raw_history(max_turns=3)
                for user_msg, bot_msg in recent_messages:
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": bot_msg})
            
            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": user_message})
            
            # 文脈を考慮した応答生成
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.85,
                presence_penalty=0.6,
                frequency_penalty=0.5,
            )
            
            bot_reply = response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"名前呼びかけ応答生成エラー: {e}")
            # エラー時は従来の方法にフォールバック
            from chatbot.name_checker import generate_himeka_response
            fallback_response = generate_himeka_response(user_message, channel_id)
            if fallback_response:
                bot_reply = fallback_response
    
    # 名前呼びかけがない場合はRAGで応答生成
    else:
        # 現在の感情状態と会話履歴を反映したプロンプトでRAG応答を生成
        bot_reply = responder.generate_response(
            user_message, 
            emotion_state=current_state,
            conversation_history=conversation_history,
            channel_id=channel_id
        )
    
    # メッセージを送信
    await message.channel.send(bot_reply)
    
    # 会話履歴に追加して感情状態を更新（新しいメッセージを追加する前に状態取得）
    emotion_tracker.add_message(user_message, bot_reply)
    
    # 名前呼びかけがあった場合は感情状態を明示的に更新
    if call_type == "sadamori_call":
        # 「定盛」と呼ばれたら強制的に怒り状態に
        emotion_tracker.anger_level += 5
        emotion_tracker._check_state_transition()
        print(f"[名前呼び] 「定盛」と呼ばれたため怒り値を上昇: {emotion_tracker.anger_level}")
    elif call_type == "himehime_call":
        # 「ひめひめ」と呼ばれたら甘え状態へ
        emotion_tracker.sweet_level += 3
        emotion_tracker._check_state_transition()
        print(f"[名前呼び] 「ひめひめ」と呼ばれたため甘え値を上昇: {emotion_tracker.sweet_level}")
    
    if emotion_tracker.get_state() != current_state:
        # 状態が変化した場合はデバッグ出力
        print(f"[感情変化] {current_state} → {emotion_tracker.get_state()} " +
              f"(怒り: {emotion_tracker.anger_level}, 甘え: {emotion_tracker.sweet_level})")

# Bot実行
client.run(DISCORD_BOT_TOKEN)
