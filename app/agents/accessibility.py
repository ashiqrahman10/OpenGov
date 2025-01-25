from gtts import gTTS
import openai

class AccessibilityAgent:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        
    def text_to_speech(self, text: str, lang: str = 'en') -> str:
        """Convert text to speech and return the file path."""
        tts = gTTS(text=text, lang=lang)
        file_path = f"static/audio/speech_{hash(text)}.mp3"
        tts.save(file_path)
        return file_path
    
    def generate_simple_summary(self, text: str) -> str:
        """Generate an easy-to-read summary using OpenAI."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Create a simple, easy-to-understand summary of the following text:"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content 