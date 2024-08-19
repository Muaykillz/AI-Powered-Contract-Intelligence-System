import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
#DEBUG
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            # Convert the response object to a dictionary using model_dump()
            response_dict = response.model_dump()
            logger.debug(f"API response: {response_dict}")
            return response_dict
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            return {"error": str(e)}

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
            {"role": "system", "content": "You are an intelligent AI assistant specialized in dividing text into logical chunks."},
            {"role": "user", "content": f"Please divide the following text into logical chunks, maintaining context:\n\n{text}\n\nChunks:"}
        ]
        result = self.call_api(messages)
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"].split("\n\n")
        return [text]
    
    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        logger.debug(f"Analyzing query: {query}")
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant specialized in analyzing user queries about procurement contracts."},
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
        # result = self.call_api(messages)
        # if "choices" in result and len(result["choices"]) > 0:
        #     return json.loads(result["choices"][0]["message"]["content"])
        # return {}
        try:
            #logger.debug("Calling API for query analysis")
            result = self.call_api(messages)
            #logger.debug(f"API response: {result}")
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                #logger.debug(f"API content response: {content}")
                
                # Try to extract JSON from the content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    #logger.debug(f"Extracted JSON string: {json_str}")
                    analysis = json.loads(json_str)
                    #logger.debug(f"Parsed analysis: {analysis}")
                    
                    # Ensure all required keys are present
                    required_keys = ["key_points", "contract_types", "keywords"]
                    for key in required_keys:
                        if key not in analysis:
                            logger.warning(f"Key '{key}' not found in analysis, adding empty list")
                            analysis[key] = []
                    
                    #logger.debug(f"Final analysis: {analysis}")
                    return analysis
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
        except Exception as e:
            logger.error(f"Error in analyze_user_query: {e}")
        
        # If anything goes wrong, return a default structure
        logger.warning("Returning default analysis structure")
        return {}
    #RAG 
    def augment_context(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        relevant_info = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        return f"Query: {query}\n\nRelevant Information:\n{relevant_info}"
    
    

    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        
        messages = [
            {"role": "system", "content": "You are an intelligent AI assistant named Bulka specialized in answering questions about procurement contracts"},
            {"role": "user", "content": 
             f"""Based on the user query, provide a detailed answer.
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
        # result = self.call_api(messages)
        # if "choices" in result and len(result["choices"]) > 0:
        #     return json.loads(result["choices"][0]["message"]["content"])
        # return {"answer": "Sorry, I couldn't generate a response.", "references": [], "confidence": 0.0}
        try:
            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                #logger.debug(f"API content response: {content}")
                
                # Try to extract JSON from the content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    # Replace any invalid control characters
                    json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
                    response_dict = json.loads(json_str)
                    #logger.debug(f"Parsed response: {response_dict}")
                    return response_dict
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
        
        # If anything goes wrong, return a default structure
        return {
            "answer": "Sorry, I couldn't generate a response due to an error.",
            "references": [],
            "confidence": 0.0
        }
    
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
    
    def check_groundedness(self, context: str, response: str) -> Dict[str, Any]:
        try:
            completion = self.client.chat.completions.create(
                model="solar-1-mini-groundedness-check",
                messages=[
                    {"role": "user", "content": context},
                    {"role": "assistant", "content": response}
                ]
            )
            
            result = json.loads(completion.choices[0].message.content)
            return {
                "score": result.get("score", 0.0),
                "feedback": result.get("feedback", "")
            }
        except Exception as e:
            print(f"Error in groundedness check: {e}")
            return {"score": 0.0, "feedback": "Error in groundedness check"}

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        logger.debug(f"Processing query: {query}")
        
        # Analyze the query
        analysis = self.analyze_user_query(query)
        #logger.debug(f"Query analysis result: {analysis}")
        
        # Generate query embedding
        query_embedding = self.embed_query(query)
        #logger.debug("Query embedding generated")
        
        # Perform hybrid search
        logger.debug("Performing hybrid search")
        search_results = vector_db.hybrid_search(
            query_embedding=query_embedding,
            keywords=analysis.get('keywords', []),  # Use .get() with a default empty list
            n_results=5
        )
        #logger.debug(f"Hybrid search results: {search_results}")
        
        # Generate response
        logger.debug("Generating response")
        response = self.generate_response(query, search_results)
        #logger.debug(f"Generated response: {response}")

        # Check groundedness
        context = "\n".join([result['document'] for result in search_results])
        groundedness_result = self.check_groundedness(context, response.get('answer', ''))
        logger.debug(f"Groundness checked")
        # Self-evaluation
        evaluation = self.self_evaluate(query, response, search_results)
        
        # If the groundedness score or evaluation score is low, try to improve the response
        if groundedness_result['score'] < 0.5 or evaluation['evaluation_score'] < 0.5:
            improved_results = vector_db.hybrid_search(
                query_embedding=query_embedding,
                keywords=analysis['keywords'],
                n_results=10
            )
            improved_response = self.generate_response(query, improved_results)
            improved_context = "\n".join([result['document'] for result in improved_results])
            improved_groundedness = self.check_groundedness(improved_context, improved_response['answer'])
            improved_evaluation = self.self_evaluate(query, improved_response, improved_results)
            
            # Use the improved response if either groundedness or evaluation score has improved
            if (improved_groundedness['score'] > groundedness_result['score'] or 
                improved_evaluation['evaluation_score'] > evaluation['evaluation_score']):
                response = improved_response
                groundedness_result = improved_groundedness
                evaluation = improved_evaluation
        
        # Combine response and evaluation
        final_result = {
                "answer": response.get('answer', "Sorry, I couldn't generate an answer."),
                "references": response.get('references', []),
                "confidence": response.get('confidence', 0.0),
                "groundedness_score": groundedness_result.get('score', 0.0),
                "groundedness_feedback": groundedness_result.get('feedback', ''),
                "evaluation_score": evaluation.get('evaluation_score', 0.0),
                "evaluation_feedback": evaluation.get('feedback', ''),
                "suggestions_for_improvement": evaluation.get('suggestions_for_improvement', [])
        }
        
        return final_result