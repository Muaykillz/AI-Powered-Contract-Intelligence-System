import uuid
from src.services.chat import Solar
import chromadb
from typing import List, Dict, Any
import os

class VectorDB:
    def __init__(self):
        persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'chroma_db')
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="contracts")
        self.solar = Solar()

    def save_to_vector_db(self, summary_result: Dict[str, Any], full_text: str) -> str:
        contract_id = str(uuid.uuid4())
        chunks = self.solar.chunk_text(full_text)
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        parties = summary_result.get("parties", [])
        parties_str = ", ".join([f"{party['name']} ({party['role']})" for party in parties])

        for i, chunk in enumerate(chunks, start=1):
            chunk_id = f"{contract_id}_chunk_{i:03d}"
            vector = self.solar.embed_document(chunk)
            
            ids.append(chunk_id)
            embeddings.append(vector)
            metadatas.append({
                "contract_id": contract_id,
                "contract_name": summary_result.get("title", ""),
                "contract_type": summary_result.get("type", ""),
                "parties": parties_str,
                "date_signed": summary_result.get("duration", {}).get("start_date", ""),
                "section": f"Chunk {i}",
                "chunk_index": i
            })
            documents.append(chunk)

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
            print("Debug: Keyword search successful")
        except Exception as e:
            print(f"Debug: Keyword search failed with error: {str(e)}")
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
    
# Create an instance of VectorDB
vector_db = VectorDB()

