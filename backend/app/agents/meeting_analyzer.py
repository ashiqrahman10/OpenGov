from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import speech_recognition as sr
from pydub import AudioSegment
import io

class MeetingAnalyzer:
    def __init__(self, groq_api_key: str, gemini_api_key: str):
        """Initialize the meeting analyzer with necessary API keys."""
        from groq import Groq
        import google.generativeai as genai
        
        self.groq_client = Groq(api_key=groq_api_key)
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        self.recognizer = sr.Recognizer()

    async def transcribe_audio(self, audio_file: bytes, file_format: str) -> str:
        """Convert audio to text using speech recognition."""
        try:
            # Convert audio file to WAV format if needed
            audio = AudioSegment.from_file(io.BytesIO(audio_file), format=file_format)
            wav_data = io.BytesIO()
            audio.export(wav_data, format="wav")
            wav_data.seek(0)
            
            # Use speech recognition
            with sr.AudioFile(wav_data) as source:
                audio_data = self.recognizer.record(source)
                transcript = self.recognizer.recognize_google(audio_data)
                return transcript
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return ""

    async def analyze_meeting(self, transcript: str) -> Dict[str, Any]:
        """Analyze meeting transcript using Groq with Gemini fallback."""
        prompt = f"""Analyze this meeting transcript and provide a structured summary:

        Transcript: "{transcript}"

        Provide the analysis in this exact JSON format:
        {{
            "summary": "brief meeting overview",
            "key_topics": [
                {{
                    "topic": "topic name",
                    "key_points": ["main points discussed"],
                    "decisions_made": ["decisions"],
                    "importance_level": "high/medium/low"
                }}
            ],
            "action_items": [
                {{
                    "task": "task description",
                    "assigned_to": "department or person",
                    "deadline": "suggested timeline",
                    "priority": "high/medium/low",
                    "resources_needed": ["required resources"]
                }}
            ],
            "participants": [
                {{
                    "name": "person name",
                    "role": "their role",
                    "contributions": ["key contributions"]
                }}
            ],
            "follow_up_needed": [
                {{
                    "item": "follow up item",
                    "responsible_party": "who needs to follow up",
                    "timeline": "when it should be done"
                }}
            ],
            "sentiment_analysis": {{
                "overall_tone": "positive/neutral/negative",
                "key_concerns": ["list of concerns"],
                "positive_highlights": ["positive aspects"]
            }}
        }}"""

        try:
            # Try Groq first
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting analyst skilled in extracting key information and action items. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
        except Exception as groq_error:
            print(f"Groq analysis error: {str(groq_error)}")
            try:
                print("Falling back to Gemini...")
                # Fallback to Gemini
                response = self.gemini_model.generate_content([
                    {
                        "role": "user",
                        "parts": [prompt]
                    }
                ])
                content = response.text.strip()
                print("Gemini analysis successful")
            except Exception as gemini_error:
                print(f"Gemini analysis error: {str(gemini_error)}")
                return self._get_default_analysis()

        try:
            # Clean response if needed
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            
            # Parse JSON
            result = json.loads(content)
            
            # Validate required fields
            required_fields = [
                "summary", "key_topics", "action_items", 
                "participants", "follow_up_needed", "sentiment_analysis"
            ]
            
            for field in required_fields:
                if field not in result:
                    print(f"Missing field {field} in response")
                    return self._get_default_analysis()
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            print(f"Raw Content: {content}")
            return self._get_default_analysis()

    async def extract_entities(self, transcript: str) -> Dict[str, List[str]]:
        """Extract named entities from the transcript."""
        prompt = f"""Extract named entities from this meeting transcript:

        Transcript: "{transcript}"

        Return in this JSON format:
        {{
            "people": ["list of people mentioned"],
            "organizations": ["list of organizations"],
            "locations": ["list of locations"],
            "dates": ["list of dates mentioned"],
            "technical_terms": ["list of technical terms"]
        }}"""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in Named Entity Recognition."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Entity extraction error: {str(e)}")
            return {
                "people": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "technical_terms": []
            }

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis structure if both Groq and Gemini fail."""
        return {
            "summary": "Analysis failed - please review transcript manually",
            "key_topics": [],
            "action_items": [],
            "participants": [],
            "follow_up_needed": [],
            "sentiment_analysis": {
                "overall_tone": "neutral",
                "key_concerns": [],
                "positive_highlights": []
            }
        }

    async def generate_meeting_minutes(self, analysis: Dict[str, Any]) -> str:
        """Generate formatted meeting minutes with Groq and Gemini fallback."""
        prompt = f"""Generate formal meeting minutes from this analysis:

        Analysis: {json.dumps(analysis, indent=2)}

        Create professional meeting minutes that include:
        1. Meeting overview
        2. Key discussions and decisions
        3. Action items and assignments
        4. Follow-up items
        5. Next steps

        Format it in a clear, professional style."""

        try:
            # Try Groq first
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional meeting minutes writer."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as groq_error:
            print(f"Groq minutes generation error: {str(groq_error)}")
            try:
                print("Falling back to Gemini for minutes generation...")
                response = self.gemini_model.generate_content([
                    {
                        "role": "user",
                        "parts": [prompt]
                    }
                ])
                return response.text
            except Exception as gemini_error:
                print(f"Gemini minutes generation error: {str(gemini_error)}")
                return "Error generating meeting minutes. Please review the analysis directly." 