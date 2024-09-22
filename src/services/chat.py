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

    def talk_general(self, text: str) -> str:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in contract-related queries."},
            {"role": "user", "content": text}
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""

    def summarize_text(self, text: str) -> str:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in extracting key information from contracts and formatting it as structured JSON. Your goal is to provide a concise yet comprehensive summary that helps readers quickly understand the main points and make informed decisions."},
            {"role": "user", "content": 
            f"""Please analyze the following contract and structure your summary in JSON format with the following elements:
                {{
                    "title": "A unique and easily understandable name for the contract",
                    "duration": {{
                        "start_date": "YYYY-MM-DD or None if not specified",
                        "end_date": "YYYY-MM-DD or 'Ongoing until terminated' if applicable",
                        "initial_term": "Initial contract duration and renewal terms if applicable"
                    }},
                    "parties": [
                        {{"name": "Party name", "role": "Role in the contract (e.g., Supplier, Distributor)"}},
                        // Add more as needed
                    ],
                    "overview": "A concise overview of the contract's purpose, main provisions, and objectives in 4-5 sentences",
                    "key_conditions": [
                        {{
                            "priority": "high/medium/low",
                            "description": "Brief detailed explanation of the condition, focusing on critical aspects for decision-making and important details for running a business (If it's exist)",
                            "potential_impact": "Potential consequences of non-compliance"
                        }},
                        // Add 5-10 key conditions, sorted by priority
                    ],
                    "important_dates": [
                        {{
                            "priority": "high/medium/low",
                            "date": "YYYY-MM-DD or description if not a specific date",
                            "description": "Description of the date's significance"
                        }},
                        // Add more as needed, excluding start and end dates
                    ],
                    "others": [
                        {{
                            "topic": "Brief topic description",
                            "details": "Important details that don't fit into other categories"
                        }},
                        // Add more as needed
                    ]
                }}
                Please ensure that:
                1. The title is unique, easily identifiable, and reflects the nature of the contract.
                2. The duration includes renewal terms if specified in the contract.
                3. The overview provides a clear and concise summary of the contract's main purpose and key provisions.
                4. Key conditions are listed in order of priority (high to low), focusing on 5-10 most critical conditions that affect contract execution.
                5. Important dates highlight key milestones and deadlines beyond the start and end dates.
                6. The 'others' section includes any crucial information that doesn't fit into the above categories but is important for understanding or executing the contract.
                7. All information is extracted directly from the contract, with no assumptions or external information added.
                8. The summary captures the most critical information for quick decision-making and risk management, with particular emphasis on detailed and comprehensive key conditions.
                9. Key conditions are analyzed thoroughly, providing enough detail for stakeholders to understand their obligations and the potential risks without needing to refer back to the full contract text.

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
            model="solar-embedding-1-large-passage",
            input=text
        )
        return response.data[0].embedding

    def embed_document(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="solar-embedding-1-large-passage",
            input=text
        )
        return response.data[0].embedding

    def chunk_text(self, text: str) -> List[Dict[str, str]]:
        messages = [
            {"role": "system", "content": """You are an AI assistant specialized in dividing text into logical chunks. Follow these guidelines:
                1. Maintain semantic coherence within each chunk.
                2. Keep related information together.
                3. Respect natural paragraph breaks where possible.
                4. Aim for chunks of roughly equal length, but prioritize coherence over strict length equality.
                5. Ensure each chunk can stand alone while maintaining context.
                6. Ideal chunk size is 100-150 words, but can vary based on content.
                7. Do not split sentences across chunks unless absolutely necessary.
                8. Provide a brief title for each chunk that summarizes its main content."""},
            {"role": "user", "content": f"""Divide the following text into logical chunks following the guidelines:

            {text}

            Output format (JSON):
            [
                {{
                    "content": "chunk content",
                    "title": "brief title summarizing the chunk"
                }},
                ...
            ]

            Please ensure that:
            1. Which chunk is important to the contract.
            2. The chunk is coherent and can stand alone.
            3. The chunk is roughly equal in length and do not more than 30 words.
            """}
        ]
        result = self.call_api(messages)
        if "choices" in result and result["choices"]:
            try:
                chunks = json.loads(result["choices"][0]["message"]["content"])
                return chunks
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in API response")
        return [{"content": text, "title": "Full Document"}]
        
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
                If the query is related to contracts, provide the following in JSON format:
                {{
                    "is_contract_related": true,
                    "key_points": ["point1", "point2", "point3"],
                    "contract_types": ["type1", "type2"],
                    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                }}

                If the query is not related to contracts, respond with:
                {{
                    "is_contract_related": false
                }}

                Pleas ensure that:
                1. The response is focused on organizational contracts and internal business operations.
                2. You accurately determine if the query is about contracts.
                3. The response is always in valid JSON format.
                4. Consider the complexity and volume of contracts typically found in large organizations.
             """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return json.loads(result["choices"][0]["message"]["content"])
        return {"is_contract_related": False}

    def augment_context(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        relevant_info = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        return f"Query: {query}\n\nRelevant Information:\n{relevant_info}"

    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        
        # print(json.dumps(search_results, indent=2))

        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in answering questions about contracts based on search results. Always respond in a valid JSON format."},
            {"role": "user", "content": 
            f"""Based on the user query and search results, provide a detailed answer.
                Include references to the source documents.

                Context: {context}
                User query: {query}

                Search results:
                {json.dumps(search_results, indent=2)}

                Respond in the following JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"file_name": "metadata['file_name']", "page": "metadata['page_number']", "relevance": "Explanation of relevance"}}
                    ],
                    "confidence": 0.0 
                }}
                
                Rules:
                1. Your entire response must be a valid JSON object.
                2. The "answer" field should contain your detailed response to the user's query.
                3. The "references" field should be an array of objects, each containing "file_name", "page" and "relevance" fields.
                4. The "confidence" field should be a number between 0 and 1, indicating your confidence in the answer.
                5. Ensure all JSON syntax is correct, including quotes around strings and proper use of commas.
                6. Do not include any text outside of the JSON object in your response.
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

    def process_query(self, prompt: str, vector_db) -> Dict[str, Any]:
        # Analyze the query
        analysis = self.analyze_user_query(prompt)
        
        # Generate query embedding
        query_embedding = self.embed_query(prompt)
        
        # Perform hybrid search
        search_results = vector_db.hybrid_search(
            query_embedding=query_embedding,
            keywords=analysis['keywords'],
            n_results=5
        )
        
        # Generate response
        response = self.generate_response(prompt, search_results)
        
        # Self-evaluation
        evaluation = self.self_evaluate(prompt, response, search_results)
        
        # If the evaluation score is low, try to improve the response
        if evaluation['evaluation_score'] < 0.7:
            improved_results = vector_db.hybrid_search(
                query_embedding=query_embedding,
                keywords=analysis['keywords'],
                n_results=10
            )
            improved_response = self.generate_response(prompt, improved_results)
            improved_evaluation = self.self_evaluate(prompt, improved_response, improved_results)
            
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