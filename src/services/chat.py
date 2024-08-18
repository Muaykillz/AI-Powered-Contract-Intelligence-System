import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
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
            {"role": "system", "content": "You are an AI assistant specialized in extracting key information from contracts and formatting it as structured JSON. Your goal is to provide a concise yet comprehensive summary that helps readers quickly understand the main points and make informed decisions."},
            {"role": "user", "content": 
            f"""Please analyze the following contract and structure your summary in JSON format with the following elements:
                {{
                    "title": "The title of the contract",
                    "duration": {{
                        "start_date": "YYYY-MM-DD or None if not specified or cannot be determined",
                        "end_date": "YYYY-MM-DD or 'Ongoing until terminated' if applicable",
                        "initial_term": "Initial contract duration"
                    }},
                    "parties": [
                        {{"name": "Party name", "role": "Role in the contract (e.g., Supplier, Distributor)"}},
                        // Add more parties as needed
                    ],
                    "overview": "A concise overview of the contract's purpose and main provisions in 4-5 sentences",
                    "key_conditions": [
                        {{
                            "priority": "high/medium/low",
                            "description": "Brief description of the condition",
                            "potential_impact": "Potential consequences of non-compliance"
                        }},
                        // Add more conditions as needed, sorted by priority
                    ],
                    "important_dates": [
                        {{
                            "priority": "high/medium/low",
                            "date": "YYYY-MM-DD or description if not a specific date or cannot be determined",
                            "description": "Description of the date's significance"
                        }},
                        // Add more dates as needed, sorted by priority
                    ]
                }}

                Please ensure that:
                1. The overview provides a clear and concise summary of the contract's main purpose and key provisions.
                2. Key conditions are listed in order of importance, focusing on those that could have significant consequences if not followed.
                3. Important dates are listed in order of priority, highlighting deadlines and key milestones.
                4. The summary captures the most critical information for quick decision-making.

                Here's the contract text to analyze:
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
    #RAG 
    def augment_context(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        relevant_info = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        return f"Query: {query}\n\nRelevant Information:\n{relevant_info}"
    
    # def adaptive_retrieval(self, query: str, vector_db, initial_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     analysis = self.analyze_user_query(query)
    #     strategy = analysis.get('retrieval_strategy', 'hybrid')
        
    #     if strategy == 'semantic':
    #         query_embedding = vector_db.solar.embed_query(query)
    #         results = vector_db.hybrid_search(query_embedding, [], n_results=10)
    #     elif strategy == 'keyword':
    #         results = vector_db.hybrid_search([], analysis['keywords'], n_results=10)
    #     else:  # hybrid (semantic and keyword)
    #         query_embedding = vector_db.solar.embed_query(query)
    #         results = vector_db.hybrid_search(query_embedding, analysis['keywords'], n_results=10)
        
    #     return results

    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in answering questions about contracts based on search results."},
            {"role": "user", "content": 
             f"""Based on the user query and search results, provide a detailed answer.
                Include references to the source documents.

                Context: {context}
                User query: {query}

                Search results:
                {json.dumps(search_results, indent=2)}

                Respond in JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"document": "doc_id", "relevance": "Explanation of relevance"}}
                    ],
                    "confidence": 0.0 
                }}
                // Confidence score between 0-1
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return json.loads(result["choices"][0]["message"]["content"])
        return {"answer": "Sorry, I couldn't generate a response.", "references": [], "confidence": 0.0}
    
    def self_evaluate(self, query: str, response: Dict[str, Any], search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in evaluating responses to contract-related queries."},
            {"role": "user", "content": 
             f"""Evaluate the following response to the user query. Consider the relevance, accuracy, and completeness of the answer based on the provided context.

                User query: {query}

                Context:
                {context}

                Response:
                {json.dumps(response, indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "evaluation_score": 0.0,  
                    "feedback": "Your detailed feedback here",
                    "suggestions_for_improvement": ["suggestion1", "suggestion2"]
                }}
                // evaluation_score should be between 0 and 1
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Try to extract JSON from the content
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in the response")
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Problematic content: {content}")
            except ValueError as e:
                print(f"Value Error: {e}")
                print(f"Problematic content: {content}")
            
            # If JSON parsing fails, return a default structure
            return {
                "evaluation_score": 0.5,
                "feedback": "Unable to parse evaluation. Please check the response format.",
                "suggestions_for_improvement": ["Ensure the response is in correct JSON format"]
            }
        
        return {"evaluation_score": 0.0, "feedback": "Unable to evaluate", "suggestions_for_improvement": []}

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        # Analyze the query
        analysis = self.analyze_user_query(query)
        
        # Generate query embedding
        query_embedding = self.embed_query(query)
        
        # Perform hybrid search
        search_results = vector_db.hybrid_search(
            query_embedding=query_embedding,
            keywords=analysis['keywords'],
            n_results=5
        )
        
        # Generate response
        response = self.generate_response(query, search_results)
        
        # Self-evaluation
        evaluation = self.self_evaluate(query, response, search_results)
        
        # If the evaluation score is low, try to improve the response
        if evaluation['evaluation_score'] < 0.7:
            improved_results = vector_db.hybrid_search(
                query_embedding=query_embedding,
                keywords=analysis['keywords'],
                n_results=10
            )
            improved_response = self.generate_response(query, improved_results)
            improved_evaluation = self.self_evaluate(query, improved_response, improved_results)
            
            if improved_evaluation['evaluation_score'] > evaluation['evaluation_score']:
                response = improved_response
                evaluation = improved_evaluation
        
        # Combine response and evaluation
        final_result = {
            "answer": response['answer'],
            "references": response['references'],
            "confidence": response.get('confidence', 0.0),
            "evaluation_score": evaluation['evaluation_score'],
            "feedback": evaluation['feedback'],
            "suggestions_for_improvement": evaluation['suggestions_for_improvement']
        }
        
        return final_result