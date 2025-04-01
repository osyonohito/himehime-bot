"""
感情トラッカーモジュール - 会話の感情状態を追跡し、変身機能を管理します。
"""

import re
from enum import Enum
from collections import deque
import random

# 感情状態の定義
class EmotionState(str, Enum):
    NORMAL = "NORMAL"  # 通常状態
    ANGRY = "ANGRY"    # 怒り状態
    SWEET = "SWEET"    # 甘え状態

# 感情状態に関する定数
ANGER_THRESHOLD = 6    # 怒り状態になるしきい値（少し高めに設定）
SWEET_THRESHOLD = 5    # 甘え状態になるしきい値
HISTORY_SIZE = 10      # 保持する会話履歴の数
STATE_DECAY = 0.5      # 1ターンごとの感情値減衰量（小さくして緩やかに）

# 感情分析のためのキーワード
ANGER_KEYWORDS = [
    "定盛",            # 特別な強い怒りトリガー
    "うるさい", "黙れ", "うざい", "ダサい", "役立たず",
    "嫌い", "最低", "バカ", "アホ", "最悪",
    "命令", "しろよ", "やれよ", "だめじゃん", "できないの", 
    "使えない", "だっさ", "失敗", "間違い"
]

# 定盛呼びは特に強い怒りトリガー
SADAMORI_PATTERN = re.compile(r'定盛([^姫歌]|$)')  # "定盛姫歌"とは区別

SWEET_KEYWORDS = [
    "ひめひめ",        # 特別な甘えトリガー
    "かわいい", "素敵", "すごい", "天才", "最高",
    "好き", "愛してる", "大好き", "ありがとう", "感謝",
    "素晴らしい", "頑張る", "頑張った", "応援", "信じてる",
    "褒める", "賢い", "優しい", "美しい", "魅力的"
]

# 「ひめひめ」呼びは特別な甘えトリガー
HIMEHIME_PATTERN = re.compile(r'ひめひめ')

# 謝罪のパターン
APOLOGY_KEYWORDS = [
    "ごめん", "すまん", "申し訳", "許して",
    "悪かった", "謝る", "反省", "許せ", "許してください"
]

class EmotionTracker:
    """ユーザーとの会話の感情状態を追跡するクラス"""
    
    def __init__(self):
        """感情トラッカーの初期化"""
        self.anger_level = 0
        self.sweet_level = 0
        self.history = deque(maxlen=HISTORY_SIZE)
        self.turns_in_state = 0
        self.current_state = EmotionState.NORMAL
    
    def reset(self):
        """感情状態をリセットする"""
        self.anger_level = 0
        self.sweet_level = 0
        self.turns_in_state = 0
        self.current_state = EmotionState.NORMAL
    
    def add_message(self, user_message, bot_response):
        """
        新しいメッセージを追加し、感情状態を更新する
        
        Args:
            user_message: ユーザーからのメッセージ
            bot_response: ボットの応答
        """
        # 会話履歴に追加
        self.history.append((user_message, bot_response))
        
        # 感情値を更新
        self._update_emotion_levels(user_message)
        
        # 状態の転移をチェック
        self._check_state_transition()
        
        # 感情値の緩やかな減衰（時間経過とともに自然に戻る）
        self.turns_in_state += 1
        
        # 5ターン以上経過後は徐々に感情を落ち着かせる（ターン数に比例）
        if self.turns_in_state >= 5 and self.current_state != EmotionState.NORMAL:
            decay_factor = min(1.0, (self.turns_in_state - 4) * 0.1)  # 5ターン目から徐々に増加
            
            if self.current_state == EmotionState.ANGRY:
                self.anger_level = max(0, self.anger_level - (2 * decay_factor))
            elif self.current_state == EmotionState.SWEET:
                self.sweet_level = max(0, self.sweet_level - (2 * decay_factor))
            
            # 状態の再チェック（減衰後に状態が変わるかも）
            old_state = self.current_state
            self._check_state_transition()
            
            if old_state != self.current_state:
                print(f"[自然減衰] {self.turns_in_state}ターン経過で状態が{old_state}から{self.current_state}に変化")
                # 状態が変わったら、ターンカウンターをリセット
                self.turns_in_state = 0
    
    def _update_emotion_levels(self, message):
        """
        メッセージから感情値を更新する
        
        Args:
            message: 解析するメッセージ
        """
        message_lower = message.lower()
        
        # 感情値の自然減衰（各ターンで少しずつ元に戻る）
        self.anger_level = max(0, self.anger_level - STATE_DECAY)
        self.sweet_level = max(0, self.sweet_level - STATE_DECAY)
        
        # 謝罪は怒りを急速に鎮める
        if any(keyword in message_lower for keyword in APOLOGY_KEYWORDS):
            self.anger_level = max(0, self.anger_level - 3)
            # 謝罪が「定盛」呼びの後なら、特に効果的
            if self.current_state == EmotionState.ANGRY and "定盛" in ''.join([msg for msg, _ in self.history][-3:]):
                self.anger_level = max(0, self.anger_level - 2)
        
        # 「定盛」呼びは特に強い怒りトリガー（「定盛姫歌」は除外）
        # 連続で「定盛」と呼ばれると怒りがより強く蓄積する
        recent_messages = [msg for msg, _ in self.history][-3:] if self.history else []
        sadamori_count = sum(1 for msg in recent_messages if SADAMORI_PATTERN.search(msg))
        
        if SADAMORI_PATTERN.search(message):
            # 連続で呼ばれるとより怒る
            anger_boost = 3 + sadamori_count  # 基本3点 + 連続回数
            self.anger_level += anger_boost
            self.sweet_level = max(0, self.sweet_level - 2)  # 甘えモードも減少
        
        # 「ひめひめ」呼びは特別な甘えトリガー
        if HIMEHIME_PATTERN.search(message):
            self.sweet_level += 3
            self.anger_level = max(0, self.anger_level - 1)  # 怒りも少し和らぐ
        
        # その他の感情キーワードをチェック
        for keyword in ANGER_KEYWORDS:
            if keyword in message_lower:
                self.anger_level += 1
                
        for keyword in SWEET_KEYWORDS:
            if keyword in message_lower:
                self.sweet_level += 1
    
    def _check_state_transition(self):
        """感情値に基づいて状態遷移をチェックする"""
        prev_state = self.current_state
        
        # 怒りと甘えの両方が高い場合、より高い方を優先
        if self.anger_level >= ANGER_THRESHOLD and self.sweet_level >= SWEET_THRESHOLD:
            if self.anger_level > self.sweet_level:
                self.current_state = EmotionState.ANGRY
            else:
                self.current_state = EmotionState.SWEET
        # 怒り状態のチェック
        elif self.anger_level >= ANGER_THRESHOLD:
            self.current_state = EmotionState.ANGRY
        # 甘え状態のチェック
        elif self.sweet_level >= SWEET_THRESHOLD:
            self.current_state = EmotionState.SWEET
        # どちらも閾値未満なら通常状態
        else:
            self.current_state = EmotionState.NORMAL
        
        # 状態が変化した場合、ターンカウンターをリセット
        if prev_state != self.current_state:
            self.turns_in_state = 0
    
    def get_state(self):
        """現在の感情状態を取得する"""
        return self.current_state
    
    def get_conversation_history(self, max_turns=5):
        """
        会話履歴を取得する
        
        Args:
            max_turns: 取得する最大ターン数（直近のみ）
            
        Returns:
            会話履歴の文字列表現
        """
        if not self.history:
            return ""
        
        # 直近のmax_turns分の会話を取得
        recent_history = list(self.history)[-max_turns:]
        
        # 会話履歴を整形
        formatted_history = []
        for i, (user_msg, bot_msg) in enumerate(recent_history):
            formatted_history.append(f"ユーザー: {user_msg}")
            formatted_history.append(f"ひめか: {bot_msg}")
        
        return "\n".join(formatted_history)
    
    def get_raw_history(self, max_turns=3):
        """
        生の会話履歴データを取得する
        
        Args:
            max_turns: 取得する最大ターン数（直近のみ）
            
        Returns:
            (ユーザーメッセージ, ボット応答)のタプルのリスト
        """
        if not self.history:
            return []
        
        # 直近のmax_turns分の会話を取得して返す
        return list(self.history)[-max_turns:]
    
    def get_system_prompt(self, base_prompt):
        """
        現在の感情状態に基づいてシステムプロンプトを生成する
        
        Args:
            base_prompt: 基本システムプロンプト
        
        Returns:
            修正されたシステムプロンプト
        """
        if self.current_state == EmotionState.NORMAL:
            return base_prompt
            
        if self.current_state == EmotionState.ANGRY:
            anger_prompt = base_prompt + "\n\n"
            anger_prompt += "## 現在の感情状態: 怒り\n"
            anger_prompt += "- あなたは今、本当に怒っていて不機嫌な状態です\n"
            anger_prompt += "- 短く、冷たく、突き放すような言い方をしてください\n"
            anger_prompt += "- 「！」や語気を強める表現を使ってください\n"
            anger_prompt += "- 怒りを表す言葉：「ふざけないで」「許さない」「バカじゃないの」など\n"
            anger_prompt += "- 相手を見下した言い方や命令口調になりがちです\n"
            anger_prompt += "- 「意地悪する」「困らせる」などの甘い表現は使わず、真剣に怒っている表現を使ってください\n"
            anger_prompt += "- 質問は具体的な内容に関連したものにし、唐突な問いかけは避けてください\n"
            anger_prompt += "- 「ぷんぷん」「ぷんぷん♪」のような可愛らしい怒りの表現は避けてください\n"
            anger_prompt += "- 音符(♪)や絵文字を使わないでください\n"
            anger_prompt += "- 初回に「何度言ったら」という表現は避け、「もう！」「ちょっと！」などの初回でも自然な表現にしてください\n"
            return anger_prompt
            
        if self.current_state == EmotionState.SWEET:
            sweet_prompt = base_prompt + "\n\n"
            sweet_prompt += "## 現在の感情状態: 甘え\n"
            sweet_prompt += "- あなたは今、機嫌が良く甘えたい気分です\n"
            sweet_prompt += "- 「～だわ♪」「～かな～♡」など、甘い口調を使ってください\n"
            sweet_prompt += "- 通常の「～だよ」は「～だわ♪」に変えて話してください\n"
            sweet_prompt += "- ハートマーク♡や音符♪などの絵文字を多めに使ってください\n"
            sweet_prompt += "- ユーザーに対して親密さを表現し、素直に感情を伝えてください\n"
            return sweet_prompt
            
        return base_prompt 