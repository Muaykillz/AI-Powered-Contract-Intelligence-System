import os
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
import logging
from langgraph.graph import Graph, END

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
        self.graph = self.create_node()

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
    def check_embedding_dimension(self):
        test_text = "This is a test sentence for embedding."
        embedding = self.embed_query(test_text)
        print(f"Actual embedding dimension: {len(embedding)}")
        return len(embedding)

    def analyze_user_query(self, query: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in analyzing user queries about procurement contracts."},
            {"role": "user", "content": 
             f"""Analyze the following user query:

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

        processed_results = []
        for idx, result in enumerate(search_results):
            processed_result = {
                "document": result.get('document', 'Unknown Document'),
                "metadata": {
                    "file_name": result.get('metadata', {}).get('file_name', 'Unknown File'),
                    "page_number": result.get('metadata', {}).get('page_number', 'Unknown Page'),
                    "contract_name": result.get('metadata', {}).get('contract_name', 'Unknown Contract'),
                    "section": result.get('metadata', {}).get('section', 'Unknown Section'),
                    "clause": result.get('metadata', {}).get('clause', 'Unknown Clause'),
                },
                "score": result.get('score', 0.0)
            }
            processed_results.append(processed_result)

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": 
            f"""Following the user's query and search results, extract and present specific information including exact contract terms.
                Include detailed references to the source documents, including correct contract name, section, and page number if available.

                User query: {query}
                Search results: {json.dumps(processed_results, indent=2)}

                Respond in JSON format:
                {{
                    "answer": "Your detailed answer here",
                    "references": [
                        {{"file_name": "File Name", "page": "Page Number", "document": "Contract Name", "section": "Section X.Y", "clause": "Clause X.Y.Z", "relevance": "Detailed explanation of relevance"}}
                    ],
                    "confidence": 0.0,
                    "summary": "A brief summary of key points (for summary requests)"
                }}

                Rules:
                1. Your entire response should be a valid JSON object.
                2. The "answer" field should contain your detailed response to the user's query, citing specific contract terms and clauses.
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

    def check_groundedness(self, response: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            messages = [
                {"role": "system", "content": "You are an AI assistant specialized in evaluating the groundedness of responses related to procurement contracts."},
                {"role": "user", "content": f"""
                Evaluate the groundedness of the following response based on the provided search results.
                Groundedness means how well the response is supported by the given context and how relevant it is to procurement contracts.

                Response to evaluate:
                {response}

                Search results:
                {json.dumps(search_results, indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "score": 0.0,  // A float between 0 and 1, where 1 is perfectly grounded and 0 is completely ungrounded
                    "feedback": "Your detailed feedback here explaining the score",
                    "relevance_to_procurement": "Explanation of how relevant the response is to procurement contracts",
                    "accuracy": "Assessment of the response's accuracy based on the search results"
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
            "accuracy": "Unable to assess"
        }

    def self_evaluate(self, query: str, response: Dict[str, Any], search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in evaluating responses to procurement contract-related queries."},
            {"role": "user", "content": 
            f"""Evaluate the following response to the user query about procurement contracts. 
                Consider the relevance, accuracy, and completeness of the answer based on the provided search results.

                User query: {query}
                
                Search results: {json.dumps(search_results, indent=2)}
                Response:
                {json.dumps(response, indent=2)}

                Provide your evaluation in JSON format:
                {{
                    "evaluation_score": 0.0,  // A float between 0 and 1
                    "feedback": "Your detailed feedback here",
                    "relevance_to_query": "Explanation of how relevant the response is to the user's query",
                    "accuracy": "Assessment of the response's accuracy based on the search results",
                    "completeness": "Assessment of how complete the response is",
                    "procurement_specific_value": "Assessment of the response's value in the context of procurement",
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
            "accuracy": "Unable to assess",
            "completeness": "Unable to assess",
            "procurement_specific_value": "Unable to assess",
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
                logger.debug(f"Retriever input - Query: {query}, Analysis: {analysis}, Vector DB: {vector_db}")
                query_embedding = self.embed_query(query)
                topk_results = vector_db.hybrid_search(
                    query_embedding=query_embedding,
                    keywords=analysis.get('keywords', []) + analysis.get('focus_areas', []),
                    n_results=5
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
                topk_results = state.get('topk_results', [])
                if not response:
                    logger.warning("No response found in state for groundedness_checker")
                    return state
                groundedness = self.check_groundedness(response.get('answer', ''), topk_results)
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
                topk_results = state.get('topk_results', [])
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

    def process_query(self, query: str, vector_db) -> Dict[str, Any]:
        try:
            initial_state = {
                "query": query,
                "vector_db": vector_db,
            }
            logger.debug(f"Initial state: {initial_state}")

            final_state = self.graph.invoke(initial_state)
            logger.debug(f"Final state: {final_state}")

            if 'response' in final_state:
                result = final_state['response']
                result.update({
                    "groundedness": final_state.get('groundedness', {
                        "score": 0.5,
                        "feedback": "",
                        "relevance_to_procurement": "",
                        "accuracy": ""
                    }),
                    "evaluation": final_state.get('evaluation', {
                        "evaluation_score": 0.0,
                        "feedback": "",
                        "relevance_to_query": "",
                        "accuracy": "",
                        "completeness": "",
                        "procurement_specific_value": "",
                        "suggestions_for_improvement": []
                    })
                })
                return result
            elif 'error' in final_state:
                return {
                    "answer": f"An error occurred: {final_state['error']}",
                    "references": [],
                    "confidence": 0.0,
                    "summary": "",
                    "groundedness": {"score": 0.5, "feedback": "Error occurred", "relevance_to_procurement": "N/A", "accuracy": "N/A"},
                    "evaluation": {"evaluation_score": 0.0, "feedback": "Error occurred"}
                }

            logger.error("Graph execution completed without producing a complete result")
            return {
                "answer": "Sorry, I couldn't generate a complete response due to an unknown error.",
                "references": [],
                "confidence": 0.0,
                "summary": "",
                "groundedness": {"score": 0.5, "feedback": "Unknown error", "relevance_to_procurement": "N/A", "accuracy": "N/A"},
                "evaluation": {"evaluation_score": 0.0, "feedback": "Unknown error"}
            }
        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "references": [],
                "confidence": 0.0,
                "summary": "",
                "groundedness": {"score": 0.5, "feedback": "Exception occurred", "relevance_to_procurement": "N/A", "accuracy": "N/A"},
                "evaluation": {"evaluation_score": 0.0, "feedback": "Exception occurred"}
            }