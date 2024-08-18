import unittest
from unittest.mock import Mock, patch
from src.services.chat import Solar
from src.database.vector_db import VectorDB

class TestRAGSystem(unittest.TestCase):

    def setUp(self):
        self.solar = Solar()
        self.vector_db = Mock(spec=VectorDB)

    @patch('src.services.chat.Solar.call_api')
    def test_process_query(self, mock_call_api):
        # Mock the API call responses
        mock_call_api.side_effect = [
            # Mock response for analyze_user_query
            {'choices': [{'message': {'content': '{"key_points": ["point1"], "contract_types": ["type1"], "keywords": ["keyword1"], "retrieval_strategy": "hybrid"}'}}]},
            # Mock response for generate_response
            {'choices': [{'message': {'content': '{"answer": "Test answer", "references": [{"document": "doc1", "relevance": "high"}], "confidence": 0.8}'}}]},
            # Mock response for self_evaluate
            {'choices': [{'message': {'content': '{"evaluation_score": 0.9, "feedback": "Good response", "suggestions_for_improvement": []}'}}]},
        ]

        # Mock VectorDB methods
        self.vector_db.search_documents.return_value = [{'document': 'Test document'}]
        self.vector_db.hybrid_search.return_value = [{'document': 'Test document'}]

        query = "What are the key terms in the contract?"
        result = self.solar.process_query(query, self.vector_db)

        # Assertions
        self.assertIn('answer', result)
        self.assertIn('evaluation_score', result)
        self.assertGreater(result['evaluation_score'], 0.5)
        self.assertEqual(result['answer'], "Test answer")
        self.assertEqual(result['confidence'], 0.8)

    def test_analyze_user_query(self):
        with patch.object(self.solar, 'call_api') as mock_call_api:
            mock_call_api.return_value = {
                'choices': [{
                    'message': {
                        'content': '{"key_points": ["point1", "point2"], "contract_types": ["type1"], "keywords": ["keyword1", "keyword2"], "retrieval_strategy": "semantic"}'
                    }
                }]
            }

            result = self.solar.analyze_user_query("Test query")

            self.assertIn('key_points', result)
            self.assertIn('contract_types', result)
            self.assertIn('keywords', result)
            self.assertIn('retrieval_strategy', result)
            self.assertEqual(result['retrieval_strategy'], 'semantic')
    def test_self_evaluate(self):
        with patch.object(self.solar, 'call_api') as mock_call_api:
            mock_call_api.return_value = {
                'choices': [{
                    'message': {
                        'content': '{"evaluation_score": 0.8, "feedback": "Good response", "suggestions_for_improvement": ["Add more detail"]}'
                    }
                }]
            }

            query = "Test query"
            response = {"answer": "Test answer", "references": []}
            search_results = [{"document": "Test document"}]

            result = self.solar.self_evaluate(query, response, search_results)

            self.assertIn('evaluation_score', result)
            self.assertIn('feedback', result)
            self.assertIn('suggestions_for_improvement', result)
            self.assertEqual(result['evaluation_score'], 0.8)
    # Add more test methods for other Solar class methods

if __name__ == '__main__':
    unittest.main()


#TODO : python -m unittest tests/test_rag_system.py