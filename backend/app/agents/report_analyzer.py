from groq import Groq
import google.generativeai as genai
from typing import Dict, List, Any
from datetime import datetime
import json

class ReportAnalyzer:
    def __init__(self, groq_api_key: str, gemini_api_key: str = None):
        self.groq_client = Groq(api_key=groq_api_key)
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        
    async def analyze_report(self, report_content: str) -> Dict[str, Any]:
        """
        Analyze corruption report content using AI to extract key information,
        categorize severity, and provide recommendations.
        """
        prompt = f"""Analyze this corruption report and provide a structured analysis in the following JSON format:

        Report Content: "{report_content}"

        The response must be a valid JSON object with these exact fields:
        {{
            "main_category": "string (e.g., financial fraud, bribery, nepotism)",
            "sub_categories": ["list", "of", "specific", "violations"],
            "severity_level": "number 1-5",
            "entities_involved": [
                {{"role": "string", "type": "string"}},
                {{"role": "string", "type": "string"}}
            ],
            "estimated_financial_impact": "number or null",
            "recommended_authorities": ["list", "of", "authorities"],
            "risk_assessment": "string description",
            "priority_level": "string (low, medium, high, urgent)",
            "potential_evidence": ["list", "of", "evidence", "types"],
            "summary": "string summary of key points"
        }}

        Ensure all fields are present and properly formatted.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert anti-corruption analyst. Always respond with properly formatted JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parse and validate response
            try:
                analysis = json.loads(response.choices[0].message.content)
                required_fields = [
                    "main_category", "sub_categories", "severity_level",
                    "entities_involved", "recommended_authorities", "risk_assessment",
                    "priority_level", "potential_evidence", "summary"
                ]
                
                # Ensure all required fields exist
                for field in required_fields:
                    if field not in analysis:
                        raise ValueError(f"Missing required field: {field}")
                
                return analysis
                
            except json.JSONDecodeError:
                raise Exception("Invalid JSON response from AI model")
                
        except Exception as e:
            if self.gemini_model:
                try:
                    response = self.gemini_model.generate_content(prompt)
                    analysis = json.loads(response.text)
                    return analysis
                except:
                    raise Exception(f"Both Groq and Gemini analysis failed: {str(e)}")
            raise e

    async def detect_sensitive_info(self, content: str) -> Dict[str, List[str]]:
        """
        Detect and flag sensitive information that should be redacted.
        """
        prompt = f"""Identify sensitive information in this text that should be redacted:

        Text: "{content}"

        Look for:
        1. Names of individuals
        2. Contact information
        3. Specific locations
        4. Financial account details
        5. Personal identification numbers
        
        Return only the lists of found items in JSON format.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data privacy expert focused on identifying sensitive information."
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
            if self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                return json.loads(response.text)
            raise e

    async def generate_report_id(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a unique, anonymous report ID that encodes key metadata.
        """
        timestamp = datetime.utcnow().strftime("%y%m%d")
        category_code = analysis['main_category'][:3].upper()
        severity = str(analysis['severity_level'])
        priority = analysis['priority_level'][:1].upper()
        
        return f"RPT-{timestamp}-{category_code}-S{severity}-P{priority}"

    async def generate_investigation_steps(self, report_content: str) -> Dict[str, Any]:
        """
        Generate investigation steps for the report.
        """
        default_response = {
            "immediate_actions": ["Review initial report", "Secure available evidence"],
            "key_witnesses": [{"role": "Primary witness", "priority": "high", "reason": "Direct knowledge of events"}],
            "required_documents": [{"document_type": "Initial report", "importance": "Foundation of investigation", "source": "System records"}],
            "investigation_timeline": [{"phase": "Initial review", "duration": "1 week", "activities": ["Document review"], "resources_needed": ["Investigator"]}],
            "potential_challenges": [{"challenge": "Evidence preservation", "mitigation": "Immediate documentation"}],
            "success_criteria": ["Complete evidence collection", "Witness cooperation"]
        }

        try:
            prompt = f"""Analyze this corruption report and provide a structured investigation plan:

            Report Content: {report_content}

            Provide your response in this EXACT JSON format:
            {{
                "immediate_actions": ["action1", "action2"],
                "key_witnesses": [
                    {{"role": "witness role", "priority": "priority level", "reason": "importance"}}
                ],
                "required_documents": [
                    {{"document_type": "type", "importance": "why needed", "source": "where to get"}}
                ],
                "investigation_timeline": [
                    {{"phase": "phase name", "duration": "time", "activities": ["activity1"], "resources_needed": ["resource1"]}}
                ],
                "potential_challenges": [
                    {{"challenge": "challenge description", "mitigation": "how to address"}}
                ],
                "success_criteria": ["criterion1", "criterion2"]
            }}"""

            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert investigator. Always respond with valid JSON matching the exact format specified."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()
            
            # Remove any markdown formatting
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()

            try:
                result = json.loads(content)
                # Validate the response has required fields
                required_fields = ["immediate_actions", "key_witnesses", "required_documents", 
                                 "investigation_timeline", "potential_challenges", "success_criteria"]
                
                for field in required_fields:
                    if field not in result:
                        print(f"Missing field {field} in response")
                        return default_response
                        
                return result
                
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
                print(f"Raw Content: {content}")
                return default_response

        except Exception as e:
            print(f"Error in generate_investigation_steps: {str(e)}")
            if self.gemini_model:
                try:
                    response = self.gemini_model.generate_content(prompt)
                    result = json.loads(response.text)
                    return result
                except:
                    return default_response
            return default_response

    async def suggest_investigation_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate suggested investigation steps based on the report analysis.
        """
        prompt = f"""Based on this corruption report analysis, suggest specific investigation steps:

        Analysis: {json.dumps(analysis)}

        Provide a detailed list of recommended investigation steps, including:
        1. Initial verification steps
        2. Evidence collection methods
        3. Stakeholders to interview
        4. Documents to request
        5. Timeline for investigation
        6. Potential challenges and mitigation strategies

        Format as a list of specific, actionable steps.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced anti-corruption investigator."
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
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                return json.loads(response.text)
            raise e

    async def assess_credibility(self, report_content: str) -> Dict[str, Any]:
        """
        Assess the credibility and completeness of the report.
        """
        try:
            prompt = f"""Analyze the credibility of this corruption report and provide a response in the following exact JSON format:

            Report: "{report_content}"

            {{
                "level_of_detail": 5,
                "internal_consistency": 5,
                "specificity": 5,
                "verifiable_elements": ["list of verifiable claims"],
                "potential_biases": ["list of biases"],
                "completeness": 5,
                "credibility_score": 50,
                "confidence_level": 50,
                "missing_information": ["list of missing details"],
                "recommendations": ["list of recommendations"]
            }}

            Return EXACTLY this format with numbers (not strings) for all numeric fields.
            """
            
            try:
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in forensic analysis. Return only the JSON object with the exact fields specified."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.1,  # Lower temperature for more consistent output
                    max_tokens=1000
                )
                
                # Default response in case of parsing failure
                default_response = {
                    "level_of_detail": 5,
                    "internal_consistency": 5,
                    "specificity": 5,
                    "verifiable_elements": ["Default verifiable elements"],
                    "potential_biases": ["Default potential biases"],
                    "completeness": 5,
                    "credibility_score": 50.0,
                    "confidence_level": 50.0,
                    "missing_information": ["Default missing information"],
                    "recommendations": ["Default recommendations"]
                }
                
                try:
                    # Get the response content
                    content = response.choices[0].message.content
                    
                    # Clean the response if needed
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:-3]  # Remove ```json and ``` markers
                    
                    # Parse the JSON
                    result = json.loads(content)
                    
                    # Ensure all required fields exist
                    for key in default_response.keys():
                        if key not in result:
                            result[key] = default_response[key]
                    
                    # Ensure credibility_score is a number
                    if not isinstance(result["credibility_score"], (int, float)):
                        result["credibility_score"] = float(result["credibility_score"])
                    
                    return result
                    
                except Exception as parse_error:
                    print(f"Error parsing Groq response: {str(parse_error)}")
                    print(f"Raw response: {content}")
                    return default_response
                
            except Exception as groq_error:
                print(f"Groq API error: {str(groq_error)}")
                if self.gemini_model:
                    try:
                        response = self.gemini_model.generate_content(prompt)
                        result = json.loads(response.text)
                        if "credibility_score" not in result:
                            result["credibility_score"] = 50.0
                        return result
                    except Exception as gemini_error:
                        print(f"Gemini API error: {str(gemini_error)}")
                        return default_response
                return default_response
            
        except Exception as e:
            print(f"General error in assess_credibility: {str(e)}")
            return {
                "level_of_detail": 5,
                "internal_consistency": 5,
                "specificity": 5,
                "verifiable_elements": ["Error occurred"],
                "potential_biases": ["Error occurred"],
                "completeness": 5,
                "credibility_score": 50.0,
                "confidence_level": 50.0,
                "missing_information": ["Error occurred"],
                "recommendations": ["Error occurred"]
            } 