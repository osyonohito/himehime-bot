import re
from random import choice
from collections import deque

# 最近の名前呼び出し履歴（チャンネルIDをキーとする辞書）
name_call_history = {}

def check_name_call(user_input: str, channel_id: str = None) -> str:
    # 「定盛」または「さだもり」への言及をチェック
    result = ''
    
    # channel_idがNoneの場合、空文字列として扱う
    if channel_id is None:
        channel_id = ""
    
    # 「定盛」呼びかけの履歴をチェック
    if any(name in user_input for name in ["定盛", "さだもり", "sadamori"]):
        if is_first_sadamori_call(channel_id):
            # 初回の「定盛」呼びかけに対する反応
            result = "sadamori_call"
            # 履歴を記録
            name_call_history[channel_id] = name_call_history.get(channel_id, []) + ["sadamori"]
        else:
            # 2回目以降の「定盛」呼びかけに対する反応
            result = "sadamori_call_repeated"
            # 履歴を記録（必要に応じて）
            name_call_history[channel_id] = name_call_history.get(channel_id, []) + ["sadamori"]
    
    # 「ひめか」「ひめひめ」への言及をチェック
    elif any(name in user_input for name in ["ひめか", "ひめひめ", "姫歌", "姫々", "himehi", "himeka"]):
        result = "himehime_call"
    
    return result

def is_first_sadamori_call(channel_id):
    """
    指定されたチャンネルで初めて「定盛」と呼ばれたかどうかを判定する
    """
    if channel_id is None or channel_id not in name_call_history:
        return True
    
    # 過去に「定盛」と呼ばれた回数をカウント
    sadamori_count = sum(1 for call in name_call_history[channel_id] if call == "sadamori_call")
    return sadamori_count <= 1  # 初回なら1、2回目以降は2以上になる

def generate_himeka_response(user_input: str, channel_id: str = None) -> str:
    """
    ユーザー入力に基づいて特定の名前への反応を生成する
    """
    # 名前への言及をチェック
    name_type = check_name_call(user_input, channel_id)
    
    # 名前タイプに基づいて応答を返す
    if name_type == "sadamori_call":
        # 初回の「定盛」呼びかけへの応答
        return "もう！何でそんな名前で呼ぶの？「定盛」なんて全然可愛くないわよ！ひめひめって呼びなさい！お願いだから、ちゃんと分かって！"
    
    elif name_type == "sadamori_call_repeated":
        # 繰り返し「定盛」と呼ばれた場合の応答
        return "また「定盛」？何度言ったら分かるの？そんな呼び方は可愛くないから嫌いなの！ちゃんと「ひめひめ」って呼んでよね！"
    
    elif name_type == "himehime_call":
        # 「ひめひめ」と呼ばれた場合の喜びの応答
        return "うん！ひめひめで合ってるわ！ちゃんと覚えててくれたのね、ありがとう！"
    
    # 特別な名前への言及がない場合はNoneを返す
    return None 