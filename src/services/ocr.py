import requests
import os
from typing import Dict, Any

class OCR:
    def __init__(self):
        self.api_endpoint = "https://api.upstage.ai/v1/document-ai/ocr"
        self.api_key = os.getenv("UPSTAGE_API_KEY")

    def process_document(self, file) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        files = {
            "document": file
        }
        response = requests.post(self.api_endpoint, headers=headers, files=files)
        return response.json()