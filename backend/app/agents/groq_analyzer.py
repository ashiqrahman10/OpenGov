from groq import Groq
from typing import Dict, Any

class GroqAnalyzer:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        
    def analyze_feedback(self, text: str) -> Dict[str, Any]:
        """Analyze feedback using Groq LLM API."""
        prompt = f"""Analyze the following feedback and provide:
        1. A sentiment score between 0 and 5 (0 being most negative, 5 being most positive)
        2. A sentiment label (positive, negative, or neutral)
        3. Key topics mentioned
        4. A brief summary
        
        Feedback: "{text}"
        
        Provide the response in this exact format:
        {{
            "sentiment_score": <score>,
            "sentiment_label": "<label>",
            "topics": ["topic1", "topic2"],
            "summary": "<brief summary>"
        }}
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI trained to analyze feedback and provide structured analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="mixtral-8x7b-32768",  # or any other Groq model
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse the response
        try:
            analysis = eval(response.choices[0].message.content)
            return analysis
        except Exception as e:
            return {
                "sentiment_score": 0.5,
                "sentiment_label": "neutral",
                "topics": ["error in analysis"],
                "summary": "Error analyzing feedback"
            } 