from transformers import pipeline
from googletrans import Translator
import spacy

class SentimentAnalysisAgent:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.translator = Translator()
        
    def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of the given text."""
        result = self.sentiment_analyzer(text)[0]
        return {
            "sentiment_label": result["label"],
            "sentiment_score": result["score"]
        }
    
    def translate_document(self, text: str, target_language: str) -> str:
        """Translate text to target language."""
        translated = self.translator.translate(text, dest=target_language)
        return translated.text 