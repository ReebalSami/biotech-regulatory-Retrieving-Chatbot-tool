from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.document_retrieval import DocumentRetrieval
from app.config import get_settings
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()

class Chatbot:
    def __init__(self, doc_retrieval: DocumentRetrieval):
        self.doc_retrieval = doc_retrieval
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
    
    def format_questionnaire_context(self, questionnaire_data: dict) -> str:
        """Format questionnaire data into a readable context"""
        if not questionnaire_data:
            return "No questionnaire data available."
        
        context = []
        for key, value in questionnaire_data.items():
            if isinstance(value, (list, tuple)):
                context.append(f"{key}: {', '.join(value)}")
            else:
                context.append(f"{key}: {value}")
        
        return "\n".join(context)
    
    def get_relevant_context(self, query: str) -> str:
        """Get relevant document context for the query"""
        try:
            documents = self.doc_retrieval.search(query)
            if not documents:
                return "No relevant documents found."
            
            context = []
            for doc in documents:
                context.append(f"Document: {doc.get('title', 'Untitled')}\n{doc.get('content', '')}\n")
            
            return "\n".join(context)
        except Exception as e:
            logger.error(f"Error retrieving document context: {str(e)}")
            return "Error retrieving document context."

    async def get_response(self, query: str, questionnaire_data: Dict = None) -> str:
        """Get a response from the chatbot"""
        try:
            # Get contexts
            questionnaire_context = self.format_questionnaire_context(questionnaire_data or {})
            document_context = self.get_relevant_context(query)
            
            # Create messages
            messages = [
                SystemMessage(content=f"""You are an AI assistant specializing in biotech regulations. 
                Use the following context to answer the user's question:
                
                Questionnaire Context:
                {questionnaire_context}
                
                Document Context:
                {document_context}
                
                Remember to:
                1. Be accurate and precise
                2. Cite specific regulations when possible
                3. Acknowledge if information is incomplete or uncertain"""),
                HumanMessage(content=query)
            ]
            
            # Get response
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting chatbot response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    async def get_response_with_context(self, query: str, context_size: int = 3) -> Dict[str, Any]:
        """
        Get a response from the chatbot based on the query and relevant documents.
        
        Args:
            query: The user's question
            context_size: Number of relevant documents to consider
            
        Returns:
            Dict containing response and relevant document sources
        """
        # Get relevant documents
        relevant_docs = self.doc_retrieval.search(query, limit=context_size)
        
        # Format documents for response
        sources = []
        for doc in relevant_docs:
            sources.append({
                "title": doc.get("title", "Unknown"),
                "content": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "jurisdiction": doc.get("jurisdiction", "Unknown")
            })
            
        # Generate response based on documents
        response = await self._generate_response(query, relevant_docs)
        
        return {
            "response": response,
            "sources": sources
        }
        
    async def _generate_response(self, query: str, relevant_docs: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the query and relevant documents.
        
        Args:
            query: The user's question
            relevant_docs: List of relevant documents
            
        Returns:
            Generated response string
        """
        # Simple response generation - can be enhanced with LLM
        if not relevant_docs:
            return "I couldn't find any relevant information in the available documents."
            
        # Create messages
        messages = [
            SystemMessage(content=f"""You are an AI assistant specializing in biotech regulations. 
            Use the following context to answer the user's question:
            
            Document Context:
            """),
            HumanMessage(content=query)
        ]
        
        for doc in relevant_docs:
            messages.append(SystemMessage(content=f"Document: {doc.get('title', 'Unknown')}\n{doc.get('content', '')}\n"))
        
        # Get response
        response = await self.llm.ainvoke(messages)
        return response.content

# Initialize chatbot with document retrieval
doc_retrieval = DocumentRetrieval()
chatbot = Chatbot(doc_retrieval)

async def process_query(query: str, context_size: int = 3) -> Dict[str, Any]:
    """
    Process a user query and return a response with relevant document sources.
    
    Args:
        query: The user's question
        context_size: Number of relevant documents to consider
        
    Returns:
        Dict containing response and relevant document sources
    """
    return await chatbot.get_response_with_context(query, context_size)
