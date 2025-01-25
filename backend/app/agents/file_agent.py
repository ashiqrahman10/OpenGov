from groq import Groq
import requests
from typing import Dict, Any
import aiohttp
import base64
import google.generativeai as genai
import io
from PyPDF2 import PdfReader
from googletrans import Translator

class FileAgent:
    def __init__(self, groq_api_key: str, gemini_api_key: str = None):
        self.groq_client = Groq(api_key=groq_api_key)
        self.translator = Translator()
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
        
    async def split_content(self, content: str, chunk_size: int = 4000) -> list[str]:
        """Split content into chunks of approximately chunk_size characters."""
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            if current_size + paragraph_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    async def extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content."""
        pdf_file = io.BytesIO(content)
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

    async def read_file_content(self, firebase_url: str, content_type: str = None) -> tuple[bytes | str, bool]:
        """Read file content from Firebase URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(firebase_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Handle different content types
                    if content_type:
                        if content_type.startswith('text/'):
                            return content.decode('utf-8'), True
                        elif content_type == 'application/pdf':
                            text = await self.extract_text_from_pdf(content)
                            return text, True
                    
                    # For other binary files
                    return content, False
                    
                raise Exception(f"Failed to read file: {response.status}")

    async def summarize_content(self, content: str, max_length: int = 500) -> str:
        """Summarize content using Groq with fallback to Gemini."""
        chunks = await self.split_content(content)
        summaries = []
        
        for chunk in chunks:
            try:
                # Try Groq first
                prompt = f"""Summarize the following content in a clear and concise way:

                {chunk}
                """
                
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a skilled summarizer that creates clear, accurate summaries."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    max_tokens=1000
                )
                
                summaries.append(response.choices[0].message.content)
                
            except Exception as e:
                if "rate_limit_exceeded" in str(e) and self.gemini_model:
                    # Fallback to Gemini if Groq hits token limit
                    try:
                        response = self.gemini_model.generate_content(prompt)
                        summaries.append(response.text)
                    except Exception as gemini_error:
                        raise Exception(f"Both Groq and Gemini failed: {str(e)} | {str(gemini_error)}")
                else:
                    raise e
    
        # If we have multiple summaries, combine them
        if len(summaries) > 1:
            combined_summary = "\n\n".join(summaries)
            # Create a final summary of the combined summaries
            final_prompt = f"""Create a final summary under {max_length} characters from these section summaries:

            {combined_summary}
            """
            
            try:
                final_response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a skilled summarizer that creates clear, accurate summaries."
                        },
                        {
                            "role": "user",
                            "content": final_prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    max_tokens=1000
                )
                return final_response.choices[0].message.content
                
            except Exception as e:
                if "rate_limit_exceeded" in str(e) and self.gemini_model:
                    response = self.gemini_model.generate_content(final_prompt)
                    return response.text
                raise e
        
        return summaries[0][:max_length]

    async def translate_content(self, content: str, target_language: str) -> str:
        """Translate content using Google Translate."""
        try:
            # Handle large content by splitting into chunks
            chunks = await self.split_content(content, chunk_size=4000)
            translated_chunks = []
            
            for chunk in chunks:
                translation = self.translator.translate(chunk, dest=target_language)
                translated_chunks.append(translation.text)
            
            return '\n\n'.join(translated_chunks)
            
        except Exception as e:
            # Fallback to Groq if Google Translate fails
            try:
                prompt = f"""Translate the following text to {target_language}:

                {content}

                Provide only the translated text without any additional comments or explanations.
                """
                
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a professional translator. Translate the text to {target_language}."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.3,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content
                
            except Exception as groq_error:
                if "rate_limit_exceeded" in str(groq_error) and self.gemini_model:
                    response = self.gemini_model.generate_content(prompt)
                    return response.text
                raise Exception(f"Translation failed: {str(e)} | Groq fallback failed: {str(groq_error)}")