from openai import OpenAI
from chatbot.character_config import CharacterConfig

class HimeResponder:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.char_config = CharacterConfig()

    def generate_response(self, user_input: str) -> str:
        try:
            messages = [
                {"role": "system", "content": self.char_config.get_system_prompt()},
                {"role": "user", "content": user_input}
            ]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"[ひめエラー] {e}")
            return "ちょっと上手く答えられなかったみたい……ごめんなさいっ！"
