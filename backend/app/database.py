from pymongo import MongoClient, ASCENDING, TEXT
from typing import Dict, List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

class Database:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['biotech_regulatory_db']
        
        # Initialize collections
        self.regulatory_documents = self.db['regulatory_documents']
        self.questionnaire_responses = self.db['questionnaire_responses']
        self.audit_logs = self.db['audit_logs']
        
        # Create indexes
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure all required indexes exist"""
        # Indexes for regulatory documents
        self.regulatory_documents.create_index([
            ("metadata.category", ASCENDING),
            ("metadata.jurisdiction", ASCENDING)
        ])
        self.regulatory_documents.create_index([
            ("content", TEXT),
            ("metadata.title", TEXT)
        ])

    def store_document(self, content: str, metadata: Dict) -> str:
        """Store a regulatory document with metadata"""
        document = {
            'content': content,
            'metadata': metadata,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'version': 1
        }
        result = self.regulatory_documents.insert_one(document)
        
        # Log the action
        self._log_audit("document_created", str(result.inserted_id))
        return str(result.inserted_id)

    def update_document(self, doc_id: str, content: str, metadata: Dict) -> bool:
        """Update an existing document"""
        try:
            doc_id = ObjectId(doc_id)
            current_doc = self.regulatory_documents.find_one({'_id': doc_id})
            if current_doc:
                update_data = {
                    'content': content,
                    'metadata': {**current_doc['metadata'], **metadata},
                    'updated_at': datetime.utcnow(),
                    'version': current_doc['version'] + 1
                }
                result = self.regulatory_documents.update_one(
                    {'_id': doc_id},
                    {'$set': update_data}
                )
                if result.modified_count > 0:
                    self._log_audit("document_updated", str(doc_id))
                    return True
            return False
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            return False

    def store_questionnaire_response(self, response: Dict) -> str:
        """Store a questionnaire response in the time series collection"""
        response['timestamp'] = datetime.utcnow()
        result = self.questionnaire_responses.insert_one(response)
        self._log_audit("questionnaire_submitted", str(result.inserted_id))
        return str(result.inserted_id)

    def _log_audit(self, action: str, reference_id: str):
        """Log an action to the audit logs collection"""
        log_entry = {
            'timestamp': datetime.utcnow(),
            'action': action,
            'reference_id': reference_id
        }
        self.audit_logs.insert_one(log_entry)

    def get_document(self, doc_id: ObjectId) -> Optional[Dict]:
        """Retrieve a document by ID"""
        try:
            if isinstance(doc_id, str):
                doc_id = ObjectId(doc_id)
            return self.regulatory_documents.find_one({'_id': doc_id})
        except Exception as e:
            print(f"Error retrieving document: {str(e)}")
            return None

    def search_documents(self, query: Dict) -> List[Dict]:
        """Search documents based on metadata criteria"""
        try:
            return list(self.regulatory_documents.find(query))
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    def text_search_documents(self, text: str) -> List[Dict]:
        """Perform a text search across documents"""
        try:
            return list(self.regulatory_documents.find(
                {"$text": {"$search": text}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]))
        except Exception as e:
            print(f"Error performing text search: {str(e)}")
            return []

# Database instance
db = Database()
