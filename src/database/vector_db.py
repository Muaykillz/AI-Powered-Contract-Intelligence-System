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

        for i, chunk in enumerate(chunks, start=1):
            chunk_id = f"{contract_id}_chunk_{i:03d}"
            vector = self.solar.embed_document(chunk)
            
            ids.append(chunk_id)
            embeddings.append(vector)
            metadatas.append({
                "contract_id": contract_id,
                "contract_name": summary_result.get("title", ""),
                "contract_type": summary_result.get("type", ""),
                "parties": ", ".join(summary_result.get("parties", "").split(", ")),
                "date_signed": summary_result.get("date", ""),
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

# Create an instance of VectorDB
vector_db = VectorDB()