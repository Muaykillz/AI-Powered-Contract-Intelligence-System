import os
from typing import List, Dict, Any
from openai import OpenAI
import json

class Solar:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is not set in environment variables")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1/solar"
        )


    def call_api(self, messages: List[Dict[str, str]], model: str = "solar-1-mini-chat") -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.dict()

    def summarize_text(self, text: str) -> str:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in extracting key information from contracts and formatting it as structured JSON."},
            {"role": "user", "content": 
             f"""Please summarize the following text and structure your summary in JSON format with the following elements:
                {{
                    "title": "The title of the contract",
                    "number": "The contract number (if available)",
                    "duration": "The duration of the contract",
                    "parties": "The parties involved in the contract",
                    "overview": "A brief overview of the contract's purpose around 4-5 sentences",
                    "conditions": [
                        {{"priority": "high/medium/low", "text": "Important condition text"}},
                        // ... more conditions as needed
                    ],
                    "dates": [
                        {{"priority": "high/medium/low", "date": "YYYY-MM-DD", "description": "Description of the date"}},
                        // ... more dates as needed
                    ]
                }}

                Here's the text to summarize:
                {text}
            """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="solar-embedding-1-large-query",
            input=text
        )
        return response.data[0].embedding

    def embed_document(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="solar-embedding-1-large-passage",
            input=text
        )
        return response.data[0].embedding

    def chunk_text(self, text: str) -> List[str]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in dividing text into logical chunks."},
            {"role": "user", "content": f"Please divide the following text into logical chunks, maintaining context:\n\n{text}\n\nChunks:"}
        ]
        result = self.call_api(messages)
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"].split("\n\n")
        return [text]
    
    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in analyzing user queries about contracts."},
            {"role": "user", "content": 
             f"""Analyze the following user query and provide:
                1. At least 3 key points to search for in contracts
                2. Possible related contract types
                3. At least 5 keywords for searching

                User query: {query}

                Respond in JSON format:
                {{
                    "key_points": ["point1", "point2", "point3"],
                    "contract_types": ["type1", "type2"],
                    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                }}
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return json.loads(result["choices"][0]["message"]["content"])
        return {}

    # ยังไม่สมบูรณ์
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in answering questions about contracts based on search results."},
            {"role": "user", "content": 
             f"""Based on the user query and search results, provide a detailed answer.
                Include references to the source documents.

                User query: {query}

                Search results:
                {json.dumps(search_results, indent=2)}

                Respond in JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"document": "doc_id", "relevance": "Explanation of relevance"}}
                    ]
                }}
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return json.loads(result["choices"][0]["message"]["content"])
        return {"answer": "Sorry, I couldn't generate a response.", "references": []}