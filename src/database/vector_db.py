import uuid
from src.services.chat import Solar
import chromadb
from typing import List, Dict, Any
import re
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import CountVectorizer

class VectorDB:
    def __init__(self, clear_on_init=False):
        persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'chroma_db')
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="contracts")
        self.solar = Solar()
        
        if clear_on_init:
            self.clear_collection()

    def semantic_splitter(self, text: str, max_chunk_size: int = 1000, min_chunk_size: int = 100, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        # แบ่งเนื้อหาเป็นส่วนๆ โดยใช้หัวข้อและการขึ้นบรรทัดใหม่
        sections = re.split(r'\n(?=[A-Z][a-z])', text)
        
        chunks = []
        for section in sections:
            # แบ่งส่วนย่อยตามย่อหน้าหรือการขึ้นบรรทัดใหม่
            paragraphs = re.split(r'\n\s*\n', section)
            
            for paragraph in paragraphs:
                # ถ้าย่อหน้ายาวเกินไป ให้แบ่งตามประโยค
                if len(paragraph) > max_chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    current_chunk = sentences[0]
                    for sentence in sentences[1:]:
                        if len(current_chunk) + len(sentence) <= max_chunk_size:
                            current_chunk += " " + sentence
                        else:
                            if len(current_chunk) >= min_chunk_size:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                    if len(current_chunk) >= min_chunk_size:
                        chunks.append(current_chunk)
                elif len(paragraph) >= min_chunk_size:
                    chunks.append(paragraph)
        
        # รวม chunks ที่สั้นเกินไปกับ chunk ถัดไป
        merged_chunks = []
        current_chunk = ""
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= max_chunk_size:
                current_chunk += " " + chunk if current_chunk else chunk
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        # ใช้ semantic similarity เพื่อรวม chunks ที่เกี่ยวข้องกัน
        if len(merged_chunks) > 1:
            embeddings = np.array([self.solar.embed_document(c) for c in merged_chunks])
            similarity_matrix = cosine_similarity(embeddings)
            
            final_chunks = []
            current_chunk = merged_chunks[0]
            for i in range(1, len(merged_chunks)):
                if similarity_matrix[i][i-1] >= similarity_threshold and len(current_chunk) + len(merged_chunks[i]) <= max_chunk_size:
                    current_chunk += " " + merged_chunks[i]
                else:
                    final_chunks.append(current_chunk)
                    current_chunk = merged_chunks[i]
            final_chunks.append(current_chunk)
        else:
            final_chunks = merged_chunks

        return [{"content": chunk.strip()} for chunk in final_chunks]

    def save_to_vector_db(self, summary_result: Dict[str, Any], ocr_result: Dict[str, Any], file_name: str) -> str:
        contract_id = str(uuid.uuid4())
        print("Start analysis for chunking...")
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        parties = summary_result.get("parties", [])
        parties_str = ", ".join([f"{party['name']} ({party['role']})" for party in parties])

        for page in ocr_result.get("pages", []):
            page_text = page.get("text", "")
            page_chunks = self.semantic_splitter(page_text)
            
            for i, chunk in enumerate(page_chunks, start=1):
                chunk_id = f"{contract_id}_page_{page['id']}_chunk_{i:03d}"
                print(f"Chunk ID: {chunk_id}, Content: {chunk['content'][:50]}...")  # Print first 50 chars for brevity
                vector = self.solar.embed_document(chunk["content"])
                
                ids.append(chunk_id)
                embeddings.append(vector)
                metadatas.append({
                    "contract_id": contract_id,
                    "contract_name": summary_result.get("title", ""),
                    "file_name": file_name,
                    "parties": parties_str,
                    "text": chunk["content"],
                    "page_number": page['id'],
                    "chunk_index": i
                })
                documents.append(chunk["content"])

        print(f"Total chunks created: {len(ids)}")

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        return contract_id

    def query_vector_db(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        query_embedding = self.solar.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results

    def get_all_documents(self) -> Dict[str, Any]:
        return self.collection.get(include=['metadatas', 'documents'])

    def search_documents(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        return self.query_vector_db(query_text, n_results)

    def semantic_search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        print(f"Debug: query_embedding length: {len(query_embedding)}")

        try:
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            print("Debug: Semantic search successful")

            # Process and format the results
            formatted_results = []
            if semantic_results['ids'] and semantic_results['ids'][0]:  # Check if results exist
                for idx in range(len(semantic_results['ids'][0])):
                    formatted_results.append({
                        'id': semantic_results['ids'][0][idx],
                        'document': semantic_results['documents'][0][idx],
                        'metadata': semantic_results['metadatas'][0][idx],
                        'score': 1 - semantic_results['distances'][0][idx]  # Convert distance to similarity score
                    })

                # Sort by score (highest first) and return top n_results
                formatted_results.sort(key=lambda x: x['score'], reverse=True)
                return formatted_results[:n_results]
            else:
                print("Debug: No results found in semantic search")
                return []

        except Exception as e:
            print(f"Debug: Semantic search failed with error: {str(e)}")
            return []  # Return an empty list if search fails

    def hybrid_search(self, analysis: Dict[str, Any], n_results: int = 5) -> List[Dict[str, Any]]:
        # Extract relevant information from the analysis
        keywords = analysis.get("keywords", [])
        key_points = analysis.get("key_points", [])
        contract_types = analysis.get("contract_types", [])

        # Combine all relevant text for semantic search
        combined_text = " ".join(keywords + key_points + contract_types)
        
        if not combined_text.strip():  # Check if combined_text is not empty or just whitespace
            print("Debug: No valid search terms found in analysis")
            return []

        # Perform semantic search
        query_embedding = self.solar.embed_query(combined_text)
        semantic_results = self.semantic_search(query_embedding, n_results * 2)  # Get more results initially

        # Perform keyword search using TF-IDF
        keyword_results = self.keyword_search(keywords + key_points, n_results * 2)

        # Combine and rank results
        combined_results = self.combine_and_rank_results(semantic_results, keyword_results, analysis)

        return combined_results[:n_results]

    def keyword_search(self, search_terms: List[str], n_results: int) -> List[Dict[str, Any]]:
        if not search_terms:
            print("Debug: No search terms provided for keyword search")
            return []

        all_docs = self.get_all_documents()
        documents = all_docs['documents']
        metadatas = all_docs['metadatas']

        if not documents:
            print("Debug: No documents found in the collection")
            return []

        # Tokenize the documents
        vectorizer = CountVectorizer(tokenizer=lambda x: x.split())
        doc_term_matrix = vectorizer.fit_transform(documents)

        # Convert sparse matrix to list of tokenized documents
        tokenized_corpus = [doc.split() for doc in documents]

        # Create BM25 object
        bm25 = BM25Okapi(tokenized_corpus)

        # Perform the search
        query = " ".join(search_terms)
        scores = bm25.get_scores(query.split())

        # Sort documents by BM25 score
        sorted_indexes = scores.argsort()[::-1]

        # Prepare results
        keyword_results = []
        for idx in sorted_indexes[:n_results]:
            keyword_results.append({
                'id': all_docs['ids'][idx],
                'document': documents[idx],
                'metadata': metadatas[idx],
                'score': scores[idx]
            })

        return keyword_results


    def combine_and_rank_results(self, semantic_results: List[Dict[str, Any]], 
                                keyword_results: List[Dict[str, Any]], 
                                analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        combined_results = {}
        
        # Helper function to calculate relevance score
        def calculate_relevance(result, analysis):
            relevance = 0
            text = result['document'].lower()
            for keyword in analysis.get('keywords', []):
                if keyword.lower() in text:
                    relevance += 1
            for key_point in analysis.get('key_points', []):
                if key_point.lower() in text:
                    relevance += 2
            for contract_type in analysis.get('contract_types', []):
                if contract_type.lower() in text:
                    relevance += 3
            return relevance

        # Function to filter out ID and chunk_index
        def filter_result(result: Dict[str, Any]) -> Dict[str, Any]:
            filtered = {k: v for k, v in result.items() if k not in ['id', 'chunk_index']}
            # Ensure 'metadata' exists and is a dictionary
            if 'metadata' in filtered and isinstance(filtered['metadata'], dict):
                filtered['metadata'] = {k: v for k, v in filtered['metadata'].items() if k not in ['chunk_index']}
            return filtered

        # Combine and score results
        for result in semantic_results + keyword_results:
            filtered_result = filter_result(result)
            key = (filtered_result.get('metadata', {}).get('contract_id', ''), 
                filtered_result.get('metadata', {}).get('page_number', ''))
            
            if key not in combined_results:
                relevance = calculate_relevance(filtered_result, analysis)
                combined_results[key] = {
                    **filtered_result,
                    'final_score': filtered_result['score'] * (1 + 0.1 * relevance)  # Boost score based on relevance
                }
            else:
                # If the document is in both results, take the higher score
                combined_results[key]['final_score'] = max(
                    combined_results[key]['final_score'],
                    filtered_result['score'] * (1 + 0.1 * calculate_relevance(filtered_result, analysis))
                )

        # Sort combined results by final_score
        sorted_results = sorted(combined_results.values(), key=lambda x: x['final_score'], reverse=True)

        return sorted_results

    def clear_collection(self):
        """Clear all data in the collection."""
        # Get all IDs in the collection
        all_ids = self.collection.get()['ids']
        
        if all_ids:
            # Delete all documents using their IDs
            self.collection.delete(ids=all_ids)
            print(f"Deleted {len(all_ids)} documents from the collection.")
        else:
            print("Collection is already empty.")

# Create an instance of VectorDB
vector_db = VectorDB(clear_on_init=True)
