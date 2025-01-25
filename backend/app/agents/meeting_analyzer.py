import openai
import whisper
import spacy
from typing import Dict, List, Any

class MeetingAnalyzer:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.whisper_model = whisper.load_model("base")
        self.nlp = spacy.load("en_core_web_sm")
        
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file to text."""
        result = self.whisper_model.transcribe(audio_file_path)
        return result["text"]
    
    def analyze_meeting(self, transcript: str) -> Dict[str, Any]:
        """Analyze meeting transcript and extract key information."""
        # Generate summary
        summary_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the key points from this meeting transcript:"},
                {"role": "user", "content": transcript}
            ]
        )
        
        # Extract action items
        action_items_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract action items from this meeting transcript:"},
                {"role": "user", "content": transcript}
            ]
        )
        
        # Extract entities (people and organizations)
        doc = self.nlp(transcript)
        entities = {
            "people": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
            "organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        }
        
        return {
            "summary": summary_response.choices[0].message.content,
            "action_items": action_items_response.choices[0].message.content,
            "entities": entities
        } 