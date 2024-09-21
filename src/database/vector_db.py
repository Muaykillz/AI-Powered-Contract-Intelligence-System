import uuid
from src.services.chat import Solar
import chromadb
from typing import List, Dict, Any
import re
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

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

            # print(semantic_results)

            # Process and format the results
            formatted_results = []
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

        except Exception as e:
            print(f"Debug: Semantic search failed with error: {str(e)}")
            return []  # Return an empty list if search fails

    def hybrid_search(self, query_embedding: List[float], keywords: List[str], n_results: int = 5) -> List[Dict[str, Any]]:
        print(f"Debug: query_embedding length: {len(query_embedding)}")
        print(f"Debug: keywords: {keywords}")

        # Perform semantic search
        try:
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # Get more results for re-ranking
                include=["documents", "metadatas", "distances"]
            )
            print("Debug: Semantic search successful")
        except Exception as e:
            print(f"Debug: Semantic search failed with error: {str(e)}")
            semantic_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Perform keyword search without embeddings
        try:
            keyword_query = " OR ".join(keywords)
            keyword_results = self.collection.query(
                query_texts=[keyword_query],
                n_results=n_results * 2,  # Get more results for re-ranking
                include=["documents", "metadatas", "distances"]
            )
            print("Debug: Keyword search successful", "results:", keyword_results)
        except Exception as e:
            print(f"Debug: Keyword search failed with error: {str(e)}")
            keyword_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


        # Perform keyword search with embeddings
        try:
            # Embed each keyword
            keyword_embeddings = [self.embed_query(keyword) for keyword in keywords]
            
            # Average the keyword embeddings
            if keyword_embeddings:
                avg_keyword_embedding = [sum(e) / len(e) for e in zip(*keyword_embeddings)]
            else:
                avg_keyword_embedding = query_embedding  # Fallback to query embedding if no keywords

            keyword_results = self.collection.query(
                query_embeddings=[avg_keyword_embedding],
                n_results=n_results * 2,  # Get more results for re-ranking
                include=["documents", "metadatas", "distances"]
            )
            print("Debug: Keyword search with embeddings successful")
        except Exception as e:
            print(f"Debug: Keyword search with embeddings failed with error: {str(e)}")
            keyword_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


        # Combine and re-rank results
        combined_results = []
        seen_ids = set()

        for sem_idx, key_idx in zip(range(len(semantic_results['ids'][0])), range(len(keyword_results['ids'][0]))):
            if sem_idx < len(semantic_results['ids'][0]):
                sem_id = semantic_results['ids'][0][sem_idx]
                if sem_id not in seen_ids:
                    seen_ids.add(sem_id)
                    combined_results.append({
                        'id': sem_id,
                        'document': semantic_results['documents'][0][sem_idx],
                        'metadata': semantic_results['metadatas'][0][sem_idx],
                        'score': 0.7 * (1 - semantic_results['distances'][0][sem_idx])  # Normalize and weight semantic score
                    })

            if key_idx < len(keyword_results['ids'][0]):
                key_id = keyword_results['ids'][0][key_idx]
                if key_id not in seen_ids:
                    seen_ids.add(key_id)
                    combined_results.append({
                        'id': key_id,
                        'document': keyword_results['documents'][0][key_idx],
                        'metadata': keyword_results['metadatas'][0][key_idx],
                        'score': 0.3 * (1 - keyword_results['distances'][0][key_idx])  # Normalize and weight keyword score
                    })

        # Sort by score and return top n_results
        combined_results.sort(key=lambda x: x['score'], reverse=True)
        return combined_results[:n_results]
    
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
vector_db = VectorDB(clear_on_init=False)
