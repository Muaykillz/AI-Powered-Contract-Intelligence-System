import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
import logging
from langgraph.graph import Graph, END
import requests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
#from src.utils.config import load_environment_variables

#load_environment_variables()
class Solar:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is not set in environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1/solar"
        )
        self.graph = self.create_node()
        #self.base_url = "https://api.upstage.ai/v1/solar"

    def call_api(self, messages: List[Dict[str, str]], model: str = "solar-1-mini-chat") -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            response_dict = response.model_dump()
            return response_dict
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            return {"error": str(e)}

    # def call_api(self, messages: List[Dict[str, str]], model: str = "solar-1-mini-chat") -> Dict[str, Any]:
    #     try:
    #         headers = {
    #             "Authorization": f"Bearer {self.api_key}",
    #             "Content-Type": "application/json"
    #         }
    #         url = f"{self.base_url}/chat/completions"
    #         data = {
    #             "model": model,
    #             "messages": messages
    #         }
    #         response = requests.post(url, headers=headers, json=data)
    #         response.raise_for_status()
    #         return response.json()
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"Error in API call: {e}")
    #         return {"error": str(e)}
        
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
    # def embed_query(self, text: str) -> List[float]:
    #     return self._create_embedding(text, "solar-embedding-1-large-query")

    # def embed_document(self, text: str) -> List[float]:
    #     return self._create_embedding(text, "solar-embedding-1-large-passage")

    # def _create_embedding(self, text: str, model: str) -> List[float]:
    #     try:
    #         headers = {
    #             "Authorization": f"Bearer {self.api_key}",
    #             "Content-Type": "application/json"
    #         }
    #         url = f"{self.base_url}/embeddings"
    #         data = {
    #             "model": model,
    #             "input": text
    #         }
    #         response = requests.post(url, headers=headers, json=data)
    #         response.raise_for_status()
    #         result = response.json()
            
    #         if "data" in result and len(result["data"]) > 0:
    #             return result["data"][0]["embedding"]
    #         else:
    #             logger.error("Unexpected response structure for embedding")
    #             return []
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"Error in embedding API call: {e}")
    #         return []
    def check_embedding_dimension(self):
        test_text = "This is a test sentence for embedding."
        embedding = self.embed_query(test_text)
        print(f"Actual embedding dimension: {len(embedding)}")
        return len(embedding)

    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in analyzing user queries about procurement contracts."},
            {"role": "user", "content": 
             f"""Analyze the following user query and provide:
                1. At least 3 key points to search for in contracts
                2. Possible related contract types
                3. At least 5 keywords for searching

                User query: {query}

                Provide the following in JSON format:
                {{
                    "is_contract_related": true,
                    "query_type": "general/summary/detailed",
                    "key_points": ["point1", "point2", "point3"],
                    "contract_types": ["type1", "type2"],
                    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                    "focus_areas": ["term1", "section1", "clause1"]
                }}

                If the query is not related to contracts, respond with:
                {{
                    "is_contract_related": false
                }}

                Ensure the response is always in valid JSON format and focused on organizational contracts and internal business operations.
             """
            }
        ]
        try:
            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                    return analysis
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except Exception as e:
            logger.error(f"Error in analyze_user_query: {e}")
        
        return {"is_contract_related": False, "query_type": "general", "key_points": [], "contract_types": [], "keywords": [], "focus_areas": []}
    def talk_general(self, text: str) -> str:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in contract-related queries."},
            {"role": "user", "content": text}
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""

    def generate_response(self, query: str, search_results: List[Dict[str, Any]], query_type: str) -> Dict[str, Any]:
        system_message = {
            "general": "You are an intelligent AI assistant specialized in answering general questions about procurement contracts.",
            "summary": "You are an intelligent AI assistant specialized in summarizing procurement contract terms and conditions.",
            "detailed": "You are an intelligent AI assistant specialized in providing detailed, specific answers and information"
        }.get(query_type, "You are an intelligent AI assistant and legal expert specialized in answering questions about procurement contracts.")
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
 

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": 
            f"""Based on the provided search results , answer the following query. 
                Include detailed references to the source documents, including correct contract name, section, and page number if available.

                User query: {query}
                Search results: {json.dumps(search_results, indent=2)}
                Context: {context}
                Respond in JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"file_name": "File Name", "page": "Page Number", "document": "Contract Name", "relevance": "Detailed explanation of relevance"}}
                    ],
                    "confidence": 0.0,
                    "summary": "A brief summary of key points (for summary requests)"
                }}

                Rules:
                1. Your entire response should be a valid JSON object.
                2. The "answer" field should contain your detailed response to the user's query, citing specific contract terms and clauses (if available).
                3. The "references" field should be an array of objects, each containing detailed information about the source.
                4. The "confidence" field should be a number between 0 and 1, indicating your confidence in the answer based on the available information.
                5. Ensure all JSON syntax is correct.
                6. Prioritize accuracy and relevance in your response.
            """
            }
        ]
        
        try:
            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
                    response_dict = json.loads(json_str)
                    return response_dict
                else:
                    logger.error("No JSON object found in the response")
            else:
                logger.error("Unexpected API response structure")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
        
        return {
            "answer": "Sorry, I couldn't generate a response.",
            "references": [],
            "confidence": 0.0,
            "summary": ""
        }

    def check_groundedness(self, response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            answer = response.get('answer', '')
            references = response.get('references', [])
            
            messages = [
                {"role": "system", "content": "You are an AI assistant specialized in evaluating the groundedness of responses related to procurement contracts."},
                {"role": "user", "content": f"""
                Evaluate the groundedness of the following response based on the provided references.
                Groundedness means how well the response is supported by the given context and how relevant it is to procurement contracts.

                Response to evaluate:
                {answer}

                References:
                {json.dumps(references, indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "score": 0.0,  // A float between 0 and 1, where 1 is perfectly grounded and 0 is completely ungrounded
                    "feedback": "Your detailed feedback here explaining the score",
                    "relevance_to_procurement": "Explanation of how relevant the response is to procurement contracts",
                
                }}
                """}
            ]

            result = self.call_api(messages)
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    evaluation = json.loads(json_str)
                    return evaluation
                else:
                    logger.error("No JSON object found in the groundedness check response")
            else:
                logger.error("Unexpected API response structure in groundedness check")
        except Exception as e:
            logger.error(f"Error in groundedness check: {e}")

        return {
            "score": 0.0,
            "feedback": "Error in groundedness check",
            "relevance_to_procurement": "Unable to determine",
            
        }
    def self_evaluate(self, query: str, response: Dict[str, Any], search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        context = "\n".join([f"Document {i+1}: {result['document']}" for i, result in enumerate(search_results)])
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in evaluating responses to procurement contract-related queries."},
            {"role": "user", "content": 
            f"""Evaluate the following response to the user query about procurement contracts. 
                Consider the relevance, accuracy, and completeness of the answer based on the provided references.

                User query: {query}
                Search results: {json.dumps(search_results, indent=2)}
                Context: {context}
                Response:
                {response.get('answer', '')}

                References:
                {json.dumps(response.get('references', []), indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "evaluation_score": 0.0,  // A float between 0 and 1
                    "feedback": "Your detailed feedback here",
                    "relevance_to_query": "Explanation of how relevant the response is to the user's query",
                    "suggestions_for_improvement": ["suggestion1", "suggestion2"]
                }}
            """
            }
        ]
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in the response")
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {e}")
                logger.error(f"Problematic content: {content}")
            except ValueError as e:
                logger.error(f"Value Error: {e}")
                logger.error(f"Problematic content: {content}")
            
        return {
            "evaluation_score": 0.5,
            "feedback": "Unable to perform a comprehensive evaluation.",
            "relevance_to_query": "Unable to determine",
            "suggestions_for_improvement": ["Ensure the response addresses procurement-specific aspects"]
        }

    def create_node(self):
        def query_analyzer(state):
            try:
                query = state['query']
                analysis = self.analyze_user_query(query)
                state['analysis'] = analysis
                return state
            except Exception as e:
                logger.error(f"Error in query_analyzer: {e}")
                state['error'] = str(e)
                return state

        def retriever(state):
            try:
                query = state['query']
                analysis = state['analysis']
                vector_db = state['vector_db']
                increase_results = state.get('increase_results', False)
                #logger.debug(f"Retriever input - Query: {query}, Analysis: {analysis}, Vector DB: {vector_db}")
                query_embedding = self.embed_query(query)
                n_results = 10 if increase_results else 5
                topk_results = vector_db.hybrid_search(
                    query_embedding=query_embedding,
                    keywords=analysis.get('keywords', []) + analysis.get('focus_areas', []),
                    n_results=n_results
                )

                if not topk_results:
                    logger.warning("No results found. Expanding search.")
                    topk_results = vector_db.hybrid_search(
                        query_embedding=query_embedding,
                        keywords=[],  # Remove keyword constraint
                        n_results=n_results * 2  # Double the number of results
                    )
                logger.debug(f"Retriever output - Detailed results: {topk_results}")
                state['topk_results'] = topk_results
                return state
            except Exception as e:
                logger.error(f"Error in retriever: {e}")
                state['error'] = str(e)
                return state

        def generator(state):
            try:
                query = state['query']
                topk_results = state['topk_results']
                query_type = state['analysis']['query_type']
                
                logger.debug(f"Generator input - Query: {query}, Query Type: {query_type}")
                logger.debug(f"Generator input - Detailed Results: {topk_results}")
                
                response = self.generate_response(query, topk_results, query_type)
                logger.debug(f"Generator output - Response: {response}")
                
                state['response'] = response
                return state
            except Exception as e:
                logger.error(f"Error in generator: {e}")
                state['error'] = str(e)
                return state

        def groundedness_checker(state):
            try:
                response = state.get('response', {})
                if not response:
                    logger.warning("No response found in state for groundedness_checker")
                    return state
                groundedness = self.check_groundedness(response)
                state['groundedness'] = groundedness
                return state
            except Exception as e:
                logger.error(f"Error in groundedness_checker: {e}")
                state['error'] = str(e)
                return state

        def evaluator(state):
            try:
                query = state['query']
                response = state.get('response', {})
                if not response:
                    logger.warning("No response found in state for evaluation")
                    return state
                topk_results = state['topk_results']
                evaluation = self.self_evaluate(query, response, topk_results)
                state['evaluation'] = evaluation
                return state
            except Exception as e:
                logger.error(f"Error in evaluator: {e}")
                state['error'] = str(e)
                return state

        workflow = Graph()
        workflow.add_node("query_analyzer", query_analyzer)
        workflow.add_node("retriever", retriever)
        workflow.add_node("generator", generator)
        workflow.add_node("groundedness_checker", groundedness_checker)
        workflow.add_node("evaluator", evaluator)

        workflow.set_entry_point("query_analyzer")
        workflow.add_edge("query_analyzer", "retriever")
        workflow.add_edge("retriever", "generator")
        workflow.add_edge("generator", "groundedness_checker")
        workflow.add_edge("groundedness_checker", "evaluator")
        workflow.add_edge("evaluator", END)

        return workflow.compile()

    def process_query(self, query: str, vector_db, refinement_count=0) -> Dict[str, Any]:
        MAX_REFINEMENT_ATTEMPTS = 3 
        CONFIDENCE_THRESHOLD = 0.55
        GROUNDEDNESS_THRESHOLD = 0.75
        try:
            initial_state = {
                "query": query,
                "vector_db": vector_db,
                "refinement_count": refinement_count
            }
            logger.debug(f"Processing query (attempt {refinement_count + 1}): {query}")

            final_state = self.graph.invoke(initial_state)

            if 'response' in final_state:
                result = final_state['response']
                groundedness = final_state.get('groundedness', {})
                
                if result['confidence'] < CONFIDENCE_THRESHOLD and refinement_count < MAX_REFINEMENT_ATTEMPTS:
                    refined_query = self.refine_query(query, result['answer'])
                    if refined_query != query:
                        logger.info(f"Refining query (attempt {refinement_count + 1})")
                        return self.process_query(refined_query, vector_db, refinement_count + 1)
                    
                if groundedness.get('score', 0) < GROUNDEDNESS_THRESHOLD and refinement_count < MAX_REFINEMENT_ATTEMPTS:
                    logger.info(f"Increasing results (attempt {refinement_count + 1})")
                    return self.increase_n_results(query, vector_db, refinement_count + 1)
                
                result.update({
                    "groundedness": groundedness,
                    "evaluation": final_state.get('evaluation', {})
                })
                return result
            elif 'error' in final_state:
                logger.error(f"Error in process_query: {final_state['error']}")
                return {
                    "answer": f"An error occurred: {final_state['error']}",
                    "references": [],
                    "confidence": 0.0,
                    "summary": "",
                    "groundedness": {"score": 0.0, "feedback": "Error occurred"},
                    "evaluation": {"evaluation_score": 0.0, "feedback": "Error occurred"}
                }
        except Exception as e:
            logger.exception(f"Unexpected error in process_query: {e}")
            return {
                "answer": f"An unexpected error occurred: {str(e)}",
                "references": [],
                "confidence": 0.0,
                "summary": "",
                "groundedness": {"score": 0.0, "feedback": "Exception occurred"},
                "evaluation": {"evaluation_score": 0.0, "feedback": "Exception occurred"}
            }
        
    def refine_query(self, original_query: str, initial_answer: str) -> str:
        
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in refining queries to extract more accurate information from a contract database."},
            {"role": "user", "content": f"""
            Based on the original query and the initial answer, generate a refined query that will help retrieve more accurate or complete information.
            
            Original Query: {original_query}
            Initial Answer: {initial_answer}
            
            Rules for refining the query:
            1. Focus on aspects of the original query that weren't fully addressed in the initial answer.
            2. If the initial answer seems incomplete, ask for more specific details.
            3. If the initial answer seems incorrect, rephrase the query to clarify the information needed.
            4. Use more specific contract-related terminology if applicable.
            5. The refined query should be a single, clear question.

            Provide only the refined query as your response.
            """}
        ]
        
        result = self.call_api(messages)
        if "choices" in result and len(result["choices"]) > 0:
            refined_query = result["choices"][0]["message"]["content"].strip()
            return refined_query
        else:
            return original_query  # Fallback to original query if refinement fails

    
    def increase_n_results(self, query: str, vector_db) -> Dict[str, Any]:
        try:
            initial_state = {
                "query": query,
                "vector_db": vector_db,
                "increase_results": True,  
                "refinement_count":0
            }
            #logger.debug(f"Reprocessing with increased results: {initial_state}")

            final_state = self.graph.invoke(initial_state)
            #logger.debug(f"Final state after reprocessing: {final_state}")
            refinement_count += 1
            if 'response' in final_state:
                result = final_state['response']
                result.update({
                    "groundedness": final_state.get('groundedness', {
                        "score": 0.5,
                        "feedback": "",
                        "relevance_to_procurement": "",
                    }),
                    "evaluation": final_state.get('evaluation', {
                        "evaluation_score": 0.0,
                        "feedback": "",
                        "relevance_to_query": "",
                        "suggestions_for_improvement": []
                    })
                })
                return result
            else:
                return {
                    "answer": "Sorry, I couldn't improve the response even with increased retrieval.",
                    "references": [],
                    "confidence": 0.0,
                    "summary": "",
                    "groundedness": {"score": 0.5, "feedback": "Reprocessing failed", "relevance_to_procurement": "N/A"},
                    "evaluation": {"evaluation_score": 0.0, "feedback": "Reprocessing failed"}
                }
        except Exception as e:
            logger.error(f"Error in reprocess_with_increased_results: {e}")
            return {
                "answer": f"An error occurred while trying to improve the response: {str(e)}",
                "references": [],
                "confidence": 0.0,
                "summary": "",
                "groundedness": {"score": 0.5, "feedback": "Exception occurred", "relevance_to_procurement": "N/A"},
                "evaluation": {"evaluation_score": 0.0, "feedback": "Exception occurred"}
            }
   

    def response_to_eval(self, query_id: str, query: str, gt_answer: str, response: Dict[str, Any]) -> Dict[str, Any]:
        # Extract the answer text
        answer_text = response.get("answer", "")
        
        # If the answer is a string representation of a dictionary, parse it
        if isinstance(answer_text, str) and answer_text.startswith('{') and answer_text.endswith('}'):
            try:
                answer_dict = json.loads(answer_text.replace("'", '"'))
                answer_text = answer_dict.get('answer', '')
            except json.JSONDecodeError:
                # If JSON parsing fails, keep the original string
                pass

        return {
            "query_id": query_id,
            "query": query,
            "gt_answer": gt_answer,
            "response": {
                "answer": answer_text,  
                "contexts": response.get("references", []),
                "confidence": response.get("confidence", 0.0),
            },
            "retrieved_context": [
                {"doc_id": f"doc_{i}", "text": ref.get("document", "")} 
                for i, ref in enumerate(response.get("references", []))
            ],
            "raw_outputs": {
                "retrieved_documents": response.get("retrieved_documents", []),
                "groundedness": response.get("groundedness", {}),
                "evaluation": response.get("evaluation", {})
            }
        }
